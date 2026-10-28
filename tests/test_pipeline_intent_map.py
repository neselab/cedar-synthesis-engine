"""End-to-end tests of the intent-map path through ``autocedar.pipeline.author``.

The map builder and condition proposer are stubs, so no model runs; Cedar and
CVC5 do run, because the path checks, merges and verifies real Cedar.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from autocedar.atoms import PropertyAtom
from autocedar.corpus import AtomDecision
from autocedar.harness.orchestrator import run_verification
from autocedar.intent_map import IntentMap, MapSentence, PermissionsQuestion
from autocedar.pipeline import MAX_CONDITION_ATTEMPTS, author
from autocedar.source_doc import compile_source_document
from tests.reviewers import approve_checked
from tests.test_intent_map import CONDITIONS, SCHEMA, SPEC, node_ids, requires_cedar, work_order_map

pytestmark = requires_cedar


def _scopes_in(packet: str) -> list[tuple[str, str]]:
    return re.findall(r"Scope (\S+): principal \S+, action (\S+), resource \S+", packet)


def _focus(packet: str) -> str:
    return re.search(r"source_id: (src\.[A-Za-z0-9_.-]+)", packet).group(1)


class Proposer:
    """Answers each condition packet with one condition atom per scope."""

    def __init__(self, doc, *, skip: set[str] = frozenset(), wrong_first: set[str] = frozenset()):
        self.text = {n.id: n.text for n in doc.nodes}
        self.skip = skip
        self.wrong_first = set(wrong_first)
        self.calls: list[tuple[str, list[AtomDecision]]] = []

    def __call__(self, packet: str, schema_path: str, prior_atoms, decisions) -> list[PropertyAtom]:
        node = _focus(packet)
        self.calls.append((node, list(decisions)))
        if node in self.skip:
            return []
        expr = next(v for k, v in CONDITIONS.items() if k in self.text[node])
        atoms = []
        for scope_id, action in _scopes_in(packet):
            if node in self.wrong_first:
                self.wrong_first.discard(node)
                action = "signoff" if action == "release" else "release"
            atoms.append(PropertyAtom(
                name=f"{action}_{expr.split('.')[-1].split()[0].lower()}",
                rationale="stub",
                plain_english_summary=expr,
                source_excerpt="",
                constraint_type="condition",
                action=action,
                principal_types=["User"],
                resource_types=["WorkOrder"],
                reference_cedar=(
                    f'permit (principal is User, action == Action::"{action}", '
                    f"resource is WorkOrder) when {{ {expr} }};"
                ),
            ))
        return atoms


def _synthesize_exact(scenario_dir: Path) -> Path:
    """Write the plan's own ceilings as the candidate: the exact policy."""
    ceilings = sorted((scenario_dir / "references").glob("ceiling__*.cedar"))
    candidate = scenario_dir / "candidate.cedar"
    candidate.write_text("\n\n".join(p.read_text() for p in ceilings) + "\n")
    return candidate


def _setup(tmp_path: Path):
    spec = tmp_path / "spec.md"
    spec.write_text(SPEC)
    schema = tmp_path / "schema.cedarschema"
    schema.write_text(SCHEMA)
    return spec, schema, compile_source_document(SPEC)


def test_mapped_run_derives_an_exact_plan_from_conditions(tmp_path: Path) -> None:
    spec, schema, doc = _setup(tmp_path)
    proposer = Proposer(doc)

    result = author(
        spec, tmp_path / "out", session_id="mapped",
        review_atom=approve_checked,
        map_intent=lambda **kw: work_order_map(doc),
        propose_property_atom=proposer,
        synthesize=_synthesize_exact,
        schema_path_override=str(schema),
    )

    assert result.notes == []
    assert result.candidate_path.is_file()
    session = result.session_dir
    plan = (session / "stage2" / "final_plan" / "verification_plan.py").read_text()
    for name in ("floor__s_release__sl_release", "ceiling__s_release",
                 "floor__s_signoff__sl_signoff", "ceiling__s_signoff",
                 "no_runtime_errors__release__User__WorkOrder"):
        assert f'"name": "{name}"' in plan
    # Each requirement was proposed once, from its own packet, in document order.
    ids = node_ids(doc)
    assert [node for node, _ in proposer.calls] == [
        ids["release:inspector"], ids["release:defect count"],
        ids["signoff:inspector"], ids["signoff:on hold"],
    ]
    assert json.loads((session / "stage2" / "map_status.json").read_text())["root_solved"] is True
    dag = json.loads((session / "stage0" / "intent_dag.json").read_text())
    assert {"and_condition_of", "or_alternative_of", "interprets"} <= {e["type"] for e in dag["edges"]}
    ledger = json.loads((session / "stage0" / "coverage_ledger.json").read_text())
    assert sorted(ledger["authorization_nodes"]) == sorted(
        ids[k] for k in ("release:inspector", "release:defect count", "signoff:inspector", "signoff:on hold")
    )
    # The candidate built from the derived ceilings passes the derived plan.
    assert run_verification(str(result.candidate_path.parent)).loss == 0


def test_requirement_without_an_approved_atom_stops_before_synthesis(tmp_path: Path) -> None:
    spec, schema, doc = _setup(tmp_path)
    ids = node_ids(doc)
    proposer = Proposer(doc, skip={ids["signoff:on hold"]})

    def must_not_synthesize(scenario_dir: Path) -> Path:
        raise AssertionError("synthesis must not start with an unsolved map")

    result = author(
        spec, tmp_path / "out", session_id="unsolved",
        review_atom=approve_checked,
        map_intent=lambda **kw: work_order_map(doc),
        propose_property_atom=proposer,
        synthesize=must_not_synthesize,
        schema_path_override=str(schema),
    )

    assert result.candidate_path == Path("")
    assert "Stopped before synthesis" in result.notes[0]
    assert ids["signoff:on hold"] in result.notes[0]
    attempts = [node for node, _ in proposer.calls if node == ids["signoff:on hold"]]
    assert len(attempts) == MAX_CONDITION_ATTEMPTS
    status = json.loads((result.session_dir / "stage2" / "map_status.json").read_text())
    assert status["blocking_conditions"] == [ids["signoff:on hold"]]


def test_wrong_action_atom_is_rejected_and_the_retry_sees_why(tmp_path: Path) -> None:
    spec, schema, doc = _setup(tmp_path)
    ids = node_ids(doc)
    first = ids["release:inspector"]
    proposer = Proposer(doc, wrong_first={first})

    result = author(
        spec, tmp_path / "out", session_id="wrong",
        review_atom=approve_checked,
        map_intent=lambda **kw: work_order_map(doc),
        propose_property_atom=proposer,
        synthesize=_synthesize_exact,
        schema_path_override=str(schema),
    )

    assert result.notes == []
    retries = [decisions for node, decisions in proposer.calls if node == first]
    assert len(retries) == 2
    assert any("map-scope: FAILED" in d.reason or "match no scope" in d.reason for d in retries[1])


def test_map_is_revised_after_structure_errors_and_review_rejection(tmp_path: Path) -> None:
    spec, schema, doc = _setup(tmp_path)
    calls: list[dict] = []

    def mapper(**kw) -> IntentMap:
        calls.append(kw)
        m = work_order_map(doc)
        if len(calls) == 1:
            m.sentences = [s for s in m.sentences if s.node_id != node_ids(doc)["signoff:on hold"]]
            m.sentences[2] = MapSentence(m.sentences[2].node_id, "condition", ["sl_nowhere"])
        return m

    map_reviews: list[str] = []

    def reviewer(atom):
        if isinstance(atom, IntentMap):
            map_reviews.append(atom.review_text)
            if len(map_reviews) == 1:
                return AtomDecision("intent_map", "reject", reason="Put the hold rule under sign off.")
            return AtomDecision("intent_map", "approve", intent_acknowledged_by_user=True)
        return approve_checked(atom)

    result = author(
        spec, tmp_path / "out", session_id="rounds",
        review_atom=reviewer,
        map_intent=mapper,
        propose_property_atom=Proposer(doc),
        synthesize=_synthesize_exact,
        schema_path_override=str(schema),
    )

    assert result.notes == []
    assert len(calls) == 3
    assert "unknown slice 'sl_nowhere'" in calls[1]["feedback"]
    assert calls[2]["feedback"] == "Put the hold rule under sign off."
    assert calls[2]["previous"] is not None
    record = json.loads((result.session_dir / "stage0" / "intent_map.json").read_text())
    assert record["approved"] is True
    assert [("structure_errors" in r, r.get("decision", {}).get("action")) for r in record["rounds"]] == [
        (True, None), (False, "reject"), (False, "approve"),
    ]
    assert "INTENT MAP" in map_reviews[0]


def test_unapproved_map_stops_before_any_atom(tmp_path: Path) -> None:
    spec, schema, doc = _setup(tmp_path)
    proposer = Proposer(doc)

    result = author(
        spec, tmp_path / "out", session_id="rejected",
        review_atom=lambda atom: AtomDecision("intent_map", "reject", reason="Wrong slices."),
        map_intent=lambda **kw: work_order_map(doc),
        propose_property_atom=proposer,
        synthesize=_synthesize_exact,
        schema_path_override=str(schema),
    )

    assert "intent map was not approved" in result.notes[0]
    assert proposer.calls == []


@pytest.mark.parametrize("marked", [None, False])
@pytest.mark.parametrize("answer", ["approve", "reject"])
def test_unmarked_scope_is_settled_by_one_yes_or_no_question(
    tmp_path: Path, answer: str, marked: bool | None,
) -> None:
    spec, schema, doc = _setup(tmp_path)
    questions: list[PermissionsQuestion] = []

    def mapper(**kw) -> IntentMap:
        # A map that calls the list "examples" without saying why is treated
        # like one that leaves it unmarked: AutoCedar asks.
        m = work_order_map(doc)
        m.scopes[1].exhaustive = marked
        return m

    def reviewer(atom):
        if isinstance(atom, PermissionsQuestion):
            questions.append(atom)
            return AtomDecision(atom.name, answer, reason="" if answer == "approve" else "Examples only.",
                                intent_acknowledged_by_user=answer == "approve")
        if isinstance(atom, IntentMap):
            assert "does not say whether all ways are listed" in atom.review_text
        return approve_checked(atom)

    result = author(
        spec, tmp_path / "out", session_id=f"question-{answer}-{marked}",
        review_atom=reviewer,
        map_intent=mapper,
        propose_property_atom=Proposer(doc),
        synthesize=_synthesize_exact if answer == "approve" else _synthesize_floors,
        schema_path_override=str(schema),
    )

    assert result.notes == []
    assert [[s.id for s in q.scopes] for q in questions] == [["s_signoff"]]
    record = json.loads((result.session_dir / "stage0" / "intent_map.json").read_text())
    assert record["permissions_complete"]["complete"] is (answer == "approve")
    assert record["permissions_complete"]["answered_by"] == "person"
    assert record["map"]["scopes"][1]["exhaustive"] is (answer == "approve")
    plan = (result.session_dir / "stage2" / "final_plan" / "verification_plan.py").read_text()
    # Yes gives the scope a ceiling equal to its floors; no leaves only the floor.
    assert ('"name": "ceiling__s_signoff"' in plan) is (answer == "approve")
    assert '"name": "floor__s_signoff__sl_signoff"' in plan


def _synthesize_floors(scenario_dir: Path) -> Path:
    """Write the plan's floors as the candidate: enough when no ceiling bounds them."""
    floors = sorted((scenario_dir / "references").glob("floor__*.cedar"))
    candidate = scenario_dir / "candidate.cedar"
    candidate.write_text("\n\n".join(p.read_text() for p in floors) + "\n")
    return candidate


def test_named_objection_is_applied_without_asking_the_mapper_again(tmp_path: Path) -> None:
    spec, schema, doc = _setup(tmp_path)
    ids = node_ids(doc)
    calls: list[dict] = []

    def mapper(**kw) -> IntentMap:
        # The classic slip: the sign-off hold rule attached to release.
        calls.append(kw)
        m = work_order_map(doc)
        hold = next(s for s in m.sentences if s.node_id == ids["signoff:on hold"])
        hold.slice_ids = ["sl_release"]
        return m

    reviews: list[str] = []

    def reviewer(atom):
        if isinstance(atom, IntentMap):
            reviews.append(atom.review_text)
            if len(reviews) == 1:
                return AtomDecision("intent_map", "reject", reason="Hold rule is under release.", edit_delta={
                    "review_channel": "model",
                    "map_objections": [{"kind": "move_condition", "node_id": ids["signoff:on hold"],
                                        "slice_ids": ["sl_signoff"], "detail": "It sits in the sign-off section."}],
                })
            return AtomDecision("intent_map", "approve", intent_acknowledged_by_user=True)
        return approve_checked(atom)

    result = author(
        spec, tmp_path / "out", session_id="objection",
        review_atom=reviewer, map_intent=mapper,
        propose_property_atom=Proposer(doc), synthesize=_synthesize_exact,
        schema_path_override=str(schema),
    )

    assert result.notes == []
    assert len(calls) == 1
    assert len(reviews) == 2
    record = json.loads((result.session_dir / "stage0" / "intent_map.json").read_text())
    assert record["rounds"][0]["objections_applied"][0]["kind"] == "move_condition"
    hold = next(s for s in record["map"]["sentences"] if s["node_id"] == ids["signoff:on hold"])
    assert hold["slice_ids"] == ["sl_signoff"]


def test_objection_the_map_cannot_apply_goes_to_the_mapper(tmp_path: Path) -> None:
    spec, schema, doc = _setup(tmp_path)
    calls: list[dict] = []

    def mapper(**kw) -> IntentMap:
        calls.append(kw)
        return work_order_map(doc)

    def reviewer(atom):
        if isinstance(atom, IntentMap) and len(calls) == 1:
            return AtomDecision("intent_map", "reject", reason="Split release.", edit_delta={
                "review_channel": "model",
                "map_objections": [{"kind": "other", "detail": "Release needs a second slice for supervisors."}],
            })
        return approve_checked(atom)

    result = author(
        spec, tmp_path / "out", session_id="objection-other",
        review_atom=reviewer, map_intent=mapper,
        propose_property_atom=Proposer(doc), synthesize=_synthesize_exact,
        schema_path_override=str(schema),
    )

    assert result.notes == []
    assert len(calls) == 2
    assert calls[1]["feedback"] == "- Release needs a second slice for supervisors."


def test_map_scope_without_a_schema_action_extends_the_schema(tmp_path: Path) -> None:
    from autocedar.atoms import ActionAtom

    spec, schema, doc = _setup(tmp_path)
    schema.write_text(SCHEMA.replace("action release, signoff", "action release"))
    requests: list[str] = []
    mapper_actions: list[str] = []

    def mapper(**kw):
        mapper_actions.append(kw["schema_actions"])
        return work_order_map(doc)

    def propose_schema_atoms(text: str):
        requests.append(text)
        return [ActionAtom(name="signoff", rationale="stub", plain_english_summary="Sign off a work order.",
                           source_excerpt="", principal_types=["User"], resource_types=["WorkOrder"])]

    def run(session_id: str, **kw):
        return author(
            spec, tmp_path / "out", session_id=session_id,
            review_atom=approve_checked,
            map_intent=mapper,
            propose_schema_atoms=propose_schema_atoms,
            propose_property_atom=Proposer(doc),
            synthesize=_synthesize_exact,
            schema_path_override=str(schema),
            **kw,
        )

    result = run("extend")

    assert result.notes == []
    assert "action signoff" in result.schema_text
    assert len(requests) == 1
    assert "action signoff, principal User, resource WorkOrder" in requests[0]
    assert "The schema can still gain actions" in mapper_actions[0]
    assert "the work order is not on hold" in requests[0]  # the sentence that needs it
    record = json.loads((result.session_dir / "stage0" / "intent_map.json").read_text())
    assert record["rounds"][0] == {
        "round": 1, "schema_extended_for": [["User", "signoff", "WorkOrder"]], "schema_refused": [], "left_out": [],
    }
    assert run_verification(str(result.candidate_path.parent)).loss == 0

    # A spent repair budget leaves the schema as it is, and the map stops on the gap.
    schema.write_text(SCHEMA.replace("action release, signoff", "action release"))
    stopped = run("fixed", max_schema_gap_repairs=0)
    assert len(requests) == 1
    assert "the schema has no action 'signoff'" in stopped.notes[0]
    assert not any("can still gain" in a for a in mapper_actions[1:])


def test_action_the_schema_review_refuses_leaves_the_map(tmp_path: Path) -> None:
    from autocedar.atoms import ActionAtom

    spec, schema, doc = _setup(tmp_path)
    schema.write_text(SCHEMA.replace("action release, signoff", "action release"))
    ids = node_ids(doc)
    map_texts: list[str] = []

    def reviewer(atom):
        if isinstance(atom, ActionAtom):
            return AtomDecision(atom.name, "reject", reason="Not an access-control requirement.")
        if isinstance(atom, IntentMap):
            map_texts.append(atom.review_text)
        return approve_checked(atom)

    result = author(
        spec, tmp_path / "out", session_id="refused",
        review_atom=reviewer,
        map_intent=lambda **_: work_order_map(doc),
        propose_schema_atoms=lambda text: [ActionAtom(
            name="signoff", rationale="stub", plain_english_summary="Sign off a work order.",
            source_excerpt="", principal_types=["User"], resource_types=["WorkOrder"])],
        propose_property_atom=Proposer(doc),
        synthesize=_synthesize_exact,
        schema_path_override=str(schema),
    )

    assert result.notes == []
    assert "signoff" not in result.schema_text
    record = json.loads((result.session_dir / "stage0" / "intent_map.json").read_text())
    assert record["rounds"][0]["schema_refused"] == [["User", "signoff", "WorkOrder"]]
    assert sorted(record["rounds"][0]["left_out"]) == sorted([ids["signoff:inspector"], ids["signoff:on hold"]])
    assert "LEFT OUT AFTER SCHEMA REVIEW" in map_texts[0] and "not on hold" in map_texts[0]
    assert [s["id"] for s in record["map"]["scopes"]] == ["s_release"]
    assert run_verification(str(result.candidate_path.parent)).loss == 0


def test_fixed_schema_turns_a_schema_gap_into_a_rewrite_of_the_atom(tmp_path: Path) -> None:
    from dataclasses import replace

    from autocedar.pipeline import PropertyRepairPlan

    spec, schema, doc = _setup(tmp_path)
    ids = node_ids(doc)
    target = ids["release:defect count"]

    class GapProposer(Proposer):
        def __call__(self, packet, schema_path, prior_atoms, decisions):
            atoms = super().__call__(packet, schema_path, prior_atoms, decisions)
            if _focus(packet) == target:
                # A field the fixed schema does not have.
                atoms = [replace(a, reference_cedar=a.reference_cedar.replace("defectCount", "openDefects"))
                         for a in atoms]
            return atoms

    instructions: list[str] = []

    def planner(text, schema_path, atom, decision, prior, schema_text, log):
        return PropertyRepairPlan(action="repair_schema", reason="needs WorkOrder.openDefects",
                                  repair_instruction="Add WorkOrder.openDefects.")

    def repairer(text, schema_path, rejected, reason, prior):
        instructions.append(reason)
        return replace(rejected, name=rejected.name + "_fixed",
                       reference_cedar=rejected.reference_cedar.replace("openDefects", "defectCount"))

    result = author(
        spec, tmp_path / "out", session_id="fixed-schema",
        review_atom=approve_checked,
        map_intent=lambda **kw: work_order_map(doc),
        propose_property_atom=GapProposer(doc),
        plan_property_repair=planner,
        repair_property_atom=repairer,
        synthesize=_synthesize_exact,
        schema_path_override=str(schema),
        max_schema_gap_repairs=0,
    )

    assert result.notes == []
    assert len(instructions) == 1 and instructions[0].startswith("The schema is fixed")
    assert run_verification(str(result.candidate_path.parent)).loss == 0


GUARD_SPEC = """# Work orders

## Permission to release a work order
Action: release
Allow this action if and only if all the following requirements hold:

- Access requires that the work order's defect count [resource.defectCount] is below 1000.
- Access requires that the work order's defect count plus one [resource.defectCount] equals 1.
"""
GUARD_SCHEMA = """entity User;
entity WorkOrder { defectCount: Long };
action release appliesTo { principal: [User], resource: [WorkOrder] };
"""
GUARD_CONDITIONS = {"below 1000": "resource.defectCount < 1000", "plus one": "resource.defectCount + 1 == 1"}


def _guard_run(tmp_path: Path, conditions: dict[str, str], session_id: str):
    from autocedar.intent_map import MapScope, MapSlice

    spec = tmp_path / "spec.md"
    spec.write_text(GUARD_SPEC)
    schema = tmp_path / "schema.cedarschema"
    schema.write_text(GUARD_SCHEMA)
    doc = compile_source_document(GUARD_SPEC)
    nodes = [n for n in doc.nodes if n.text.startswith("- ")]
    intent_map = IntentMap(
        scopes=[MapScope("s_release", "release", "User", "WorkOrder", True)],
        slices=[MapSlice("sl_release", "s_release", "release")],
        sentences=[MapSentence(n.id, "condition", ["sl_release"]) for n in nodes],
    )
    text = {n.id: n.text for n in doc.nodes}

    def proposer(packet, schema_path, prior_atoms, decisions):
        node = _focus(packet)
        expr = next(v for k, v in conditions.items() if k in text[node])
        return [PropertyAtom(
            name=f"release_{len(prior_atoms)}_{len(decisions)}", rationale="stub",
            plain_english_summary=expr, source_excerpt="", constraint_type="condition",
            action="release", principal_types=["User"], resource_types=["WorkOrder"],
            reference_cedar=f'permit (principal is User, action == Action::"release", '
                            f"resource is WorkOrder) when {{ {expr} }};",
        )]

    return author(
        spec, tmp_path / "out", session_id=session_id,
        review_atom=approve_checked, map_intent=lambda **kw: intent_map,
        propose_property_atom=proposer, synthesize=_synthesize_exact,
        schema_path_override=str(schema),
    )


def test_atom_that_can_overflow_alone_is_safe_after_the_earlier_range_check(tmp_path: Path) -> None:
    from autocedar.intent_map import GUARDED_BY_SLICE

    result = _guard_run(tmp_path, GUARD_CONDITIONS, "guarded")

    assert result.notes == []
    arithmetic = next(a for a in result.plan.properties if "+ 1" in a.reference_cedar)
    assert GUARDED_BY_SLICE in arithmetic.symbolic_verification_log
    floor = (result.session_dir / "stage2" / "final_plan" / "references").glob("floor__*.cedar")
    text = " ".join(next(floor).read_text().split())
    assert text.index("< 1000") < text.index("+ 1")
    # The calculated plan, used as the candidate, never raises a runtime error.
    assert run_verification(str(result.candidate_path.parent)).loss == 0


def test_atom_that_can_overflow_without_a_guard_is_still_rejected(tmp_path: Path) -> None:
    unguarded = {"below 1000": "resource.defectCount + 1 == 1", "plus one": "resource.defectCount + 1 == 1"}

    result = _guard_run(tmp_path, unguarded, "unguarded")

    assert result.candidate_path == Path("")
    assert "Stopped before synthesis" in result.notes[0]
