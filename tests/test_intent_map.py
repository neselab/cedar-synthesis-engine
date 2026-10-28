"""Unit tests for ``autocedar.intent_map``: structure checks, node status,
map-scoped packets, condition shape, and calculated floors and ceilings."""

from __future__ import annotations

import os
import re
import subprocess
import textwrap
from pathlib import Path

import pytest

from autocedar.atoms import PropertyAtom
from autocedar.grounding import CEDAR_PATH, CVC5_PATH
from autocedar.intent_map import (
    IntentMap,
    MapScope,
    MapSentence,
    MapSlice,
    PermissionsQuestion,
    build_condition_packet,
    condition_atom_issue,
    condition_shape_issue,
    derive_boundary_atoms,
    schema_triples,
)
from autocedar.source_doc import attach_source_ids, compile_source_document

requires_cedar = pytest.mark.skipif(
    not (os.access(CEDAR_PATH, os.X_OK) and os.access(CVC5_PATH, os.X_OK)),
    reason="Cedar/CVC5 not available",
)

SPEC = textwrap.dedent("""\
    # Work orders

    ## Permission to release a work order
    Action: release
    Allow this action if and only if all the following requirements hold:

    - Access requires that the user [principal] equals the work order's inspector [resource.inspector].
    - Access requires that the work order's defect count [resource.defectCount] equals 0.

    ## Permission to sign off a work order
    Action: signoff
    Allow this action if and only if all the following requirements hold:

    - Access requires that the user [principal] equals the work order's inspector [resource.inspector].
    - Access requires that the work order is not on hold [resource.onHold].

    ## How permissions apply
    Each unless clause waives only the requirement in its own sentence.
""")

SCHEMA = textwrap.dedent("""\
    entity User;
    entity WorkOrder { inspector: User, defectCount: Long, onHold: Bool };
    action release, signoff appliesTo { principal: [User], resource: [WorkOrder] };
""")

CONDITIONS = {
    "inspector": "principal == resource.inspector",
    "defect count": "resource.defectCount == 0",
    "on hold": "!resource.onHold",
}


def node_ids(doc) -> dict[str, str]:
    """Short names for the spec's nodes."""
    ids = {}
    for node in doc.nodes:
        section = node.heading_path[1] if len(node.heading_path) > 1 else ""
        action = "release" if "release" in section else "signoff" if "sign off" in section else "rules"
        if node.text.startswith("- "):
            key = next(k for k in CONDITIONS if k in node.text)
            ids[f"{action}:{key}"] = node.id
        elif "unless clause" in node.text:
            ids["rule"] = node.id
    return ids


def work_order_map(doc) -> IntentMap:
    ids = node_ids(doc)
    return IntentMap(
        scopes=[
            MapScope("s_release", "release", "User", "WorkOrder", True, "Release"),
            MapScope("s_signoff", "signoff", "User", "WorkOrder", True, "Sign off"),
        ],
        slices=[
            MapSlice("sl_release", "s_release", "inspector releases a clean work order"),
            MapSlice("sl_signoff", "s_signoff", "inspector signs off an order not on hold"),
        ],
        sentences=[
            MapSentence(ids["release:inspector"], "condition", ["sl_release"]),
            MapSentence(ids["release:defect count"], "condition", ["sl_release"]),
            MapSentence(ids["signoff:inspector"], "condition", ["sl_signoff"]),
            MapSentence(ids["signoff:on hold"], "condition", ["sl_signoff"]),
            MapSentence(ids["rule"], "interpretation"),
        ],
    )


def condition_atom(node_id: str, action: str, expr: str, name: str = "") -> PropertyAtom:
    atom = PropertyAtom(
        name=name or f"{action}_{re.sub(r'[^a-z]+', '_', expr.lower()).strip('_')}",
        rationale="test",
        plain_english_summary=expr,
        source_excerpt=f"[source_id: {node_id}]",
        constraint_type="condition",
        action=action,
        principal_types=["User"],
        resource_types=["WorkOrder"],
        reference_cedar=(
            f'permit (principal is User, action == Action::"{action}", resource is WorkOrder) '
            f"when {{ {expr} }};"
        ),
        symbolic_verified=True,
    )
    return attach_source_ids(atom, [node_id])


TRIPLES = {("User", "release", "WorkOrder"), ("User", "signoff", "WorkOrder")}


def test_identical_sentences_in_two_sections_are_two_nodes() -> None:
    ids = node_ids(compile_source_document(SPEC))
    assert ids["release:inspector"] != ids["signoff:inspector"]


def test_well_formed_map_passes_structure_checks() -> None:
    doc = compile_source_document(SPEC)
    assert work_order_map(doc).structure_errors(doc, TRIPLES) == []


def test_structure_checks_name_each_problem() -> None:
    doc = compile_source_document(SPEC)
    m = work_order_map(doc)
    m.scopes.append(MapScope("s_delete", "delete", "User", "WorkOrder"))
    m.slices.append(MapSlice("sl_empty", "s_release"))
    m.sentences.append(MapSentence("src.unknown.p9999.l1", "condition", ["sl_missing"]))
    m.sentences.append(MapSentence(m.sentences[0].node_id, "interpretation"))

    errors = "\n".join(m.structure_errors(doc, TRIPLES))

    assert "no action 'delete'" in errors
    assert "Slice 'sl_empty' has no condition" in errors
    assert "Unknown source node 'src.unknown.p9999.l1'" in errors
    assert "unknown slice 'sl_missing'" in errors
    assert "classified more than once" in errors


def test_condition_is_solved_only_with_an_approved_atom_per_scope() -> None:
    doc = compile_source_document(SPEC)
    m = work_order_map(doc)
    ids = node_ids(doc)
    atoms = [condition_atom(ids["release:inspector"], "release", CONDITIONS["inspector"])]

    status = m.status(atoms)

    assert status["conditions"][ids["release:inspector"]] == {"s_release": True}
    assert status["slices"] == {"sl_release": False, "sl_signoff": False}
    assert status["root_solved"] is False
    assert ids["release:defect count"] in status["blocking_conditions"]

    atoms += [
        condition_atom(ids["release:defect count"], "release", CONDITIONS["defect count"]),
        condition_atom(ids["signoff:inspector"], "signoff", CONDITIONS["inspector"]),
        condition_atom(ids["signoff:on hold"], "signoff", CONDITIONS["on hold"]),
    ]
    assert m.status(atoms)["root_solved"] is True


def test_atom_for_the_wrong_action_does_not_solve_a_condition() -> None:
    doc = compile_source_document(SPEC)
    m = work_order_map(doc)
    ids = node_ids(doc)
    wrong = condition_atom(ids["release:inspector"], "signoff", CONDITIONS["inspector"])

    assert "match no scope" in condition_atom_issue(m, wrong, ids["release:inspector"])
    assert m.unsolved_scopes(ids["release:inspector"], [wrong])[0].id == "s_release"


def test_packet_holds_the_slice_siblings_and_rules_but_not_the_other_action() -> None:
    doc = compile_source_document(SPEC)
    m = work_order_map(doc)
    ids = node_ids(doc)
    node = doc.by_id[ids["release:inspector"]]

    packet = build_condition_packet(doc, m, node, [], step=1)

    assert "<autocedar_condition_packet" in packet.text
    assert "Scope s_release: principal User, action release, resource WorkOrder" in packet.text
    assert ids["release:defect count"] in packet.text
    assert ids["rule"] in packet.text
    assert ids["signoff:inspector"] not in packet.text
    assert ids["signoff:on hold"] not in packet.text
    assert {n.id for n in packet.related_nodes} == {ids["release:defect count"], ids["rule"]}


def test_render_lists_every_sentence_once() -> None:
    doc = compile_source_document(SPEC)
    text = work_order_map(doc).render(doc)

    assert "Scope s_release" in text and "Scope s_signoff" in text
    assert "Rules for interpretation" in text
    assert "Sentences with no requirement" in text
    assert "Action: release" in text  # the label line carries no requirement


@requires_cedar
def test_schema_triples_reads_actions_from_the_schema() -> None:
    assert schema_triples(SCHEMA, cedar_path=CEDAR_PATH) >= TRIPLES


@requires_cedar
@pytest.mark.parametrize(
    "cedar, expected",
    [
        ('permit (principal is User, action == Action::"release", resource is WorkOrder) when { true };', ""),
        ('permit (principal, action == Action::"release", resource) when { true };', ""),
        ('forbid (principal, action == Action::"release", resource) when { true };', "permit policy"),
        ('permit (principal, action == Action::"signoff", resource) when { true };', "action must be"),
        ('permit (principal, action == Action::"release", resource);', "when or unless"),
        (
            'permit (principal, action == Action::"release", resource) when { true };\n'
            'permit (principal, action == Action::"release", resource) when { false };',
            "exactly one policy",
        ),
    ],
)
def test_condition_shape(cedar: str, expected: str) -> None:
    atom = condition_atom("src.x", "release", "true")
    issue = condition_shape_issue(cedar, atom, CEDAR_PATH)
    assert (expected in issue) if expected else issue == ""


@requires_cedar
def test_floors_and_ceilings_are_calculated_from_approved_conditions(tmp_path: Path) -> None:
    doc = compile_source_document(SPEC)
    m = work_order_map(doc)
    ids = node_ids(doc)
    atoms = [
        condition_atom(ids["release:inspector"], "release", CONDITIONS["inspector"]),
        condition_atom(ids["release:defect count"], "release", CONDITIONS["defect count"]),
        condition_atom(ids["signoff:inspector"], "signoff", CONDITIONS["inspector"]),
        condition_atom(ids["signoff:on hold"], "signoff", CONDITIONS["on hold"]),
    ]

    derived, issues = derive_boundary_atoms(m, atoms, cedar_path=CEDAR_PATH)

    assert issues == []
    by_name = {a.name: a for a in derived}
    assert set(by_name) == {
        "floor__s_release__sl_release", "ceiling__s_release",
        "floor__s_signoff__sl_signoff", "ceiling__s_signoff",
    }
    release_floor = by_name["floor__s_release__sl_release"].reference_cedar
    assert "resource.inspector" in release_floor and "resource.defectCount" in release_floor
    assert "onHold" not in release_floor
    assert by_name["ceiling__s_release"].reference_cedar == release_floor
    schema = tmp_path / "schema.cedarschema"
    schema.write_text(SCHEMA)
    for atom in derived:
        policy = tmp_path / f"{atom.name}.cedar"
        policy.write_text(atom.reference_cedar)
        result = subprocess.run(
            [CEDAR_PATH, "validate", "--schema", str(schema), "--policies", str(policy)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, result.stdout + result.stderr


@requires_cedar
def test_condition_with_a_long_chain_merges_into_a_valid_floor(tmp_path: Path) -> None:
    # The JSON form of 70 chained || nests past the 128 levels Cedar's JSON reader allows.
    chain = " || ".join(f"resource.defectCount == {k}" for k in range(70))
    doc = compile_source_document(SPEC)
    m = work_order_map(doc)
    ids = node_ids(doc)
    atoms = [
        condition_atom(ids["release:inspector"], "release", CONDITIONS["inspector"]),
        condition_atom(ids["release:defect count"], "release", chain, name="release_defects"),
    ]

    derived, issues = derive_boundary_atoms(m, atoms, cedar_path=CEDAR_PATH)

    floor = next(a for a in derived if a.name == "floor__s_release__sl_release").reference_cedar
    assert not any("sl_release" in issue for issue in issues)
    assert floor.index("resource.inspector") < floor.index("resource.defectCount == 69")
    schema = tmp_path / "schema.cedarschema"
    schema.write_text(SCHEMA)
    policy = tmp_path / "floor.cedar"
    policy.write_text(floor)
    result = subprocess.run(
        [CEDAR_PATH, "validate", "--schema", str(schema), "--policies", str(policy)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@requires_cedar
def test_missing_condition_atom_is_reported_not_guessed() -> None:
    doc = compile_source_document(SPEC)
    m = work_order_map(doc)
    ids = node_ids(doc)
    atoms = [condition_atom(ids["release:inspector"], "release", CONDITIONS["inspector"])]

    derived, issues = derive_boundary_atoms(m, atoms, cedar_path=CEDAR_PATH)

    assert any("sl_release" in issue for issue in issues)
    assert not any(a.name.startswith("floor__s_release") for a in derived)


@requires_cedar
def test_examples_only_scope_keeps_whole_scope_restrictions_as_ceilings() -> None:
    doc = compile_source_document(SPEC)
    ids = node_ids(doc)
    m = IntentMap(
        scopes=[MapScope("s_release", "release", "User", "WorkOrder", exhaustive=False)],
        slices=[MapSlice("sl_inspector", "s_release")],
        sentences=[
            MapSentence(ids["release:inspector"], "condition", ["sl_inspector"]),
            MapSentence(ids["release:defect count"], "condition", restricts_scope_ids=["s_release"]),
        ],
    )
    atoms = [
        condition_atom(ids["release:inspector"], "release", CONDITIONS["inspector"]),
        condition_atom(ids["release:defect count"], "release", CONDITIONS["defect count"]),
    ]

    derived, issues = derive_boundary_atoms(m, atoms, cedar_path=CEDAR_PATH)

    assert issues == []
    kinds = {a.name: a.constraint_type for a in derived}
    assert kinds == {
        "floor__s_release__sl_inspector": "floor",
        f"ceiling__s_release__{ids['release:defect count'].replace('.', '_').lower()}": "ceiling",
    }
    floor = next(a for a in derived if a.constraint_type == "floor").reference_cedar
    assert "defectCount" in floor  # the restriction is part of every slice


def test_unmarked_scopes_render_as_not_stated_and_survive_a_round_trip() -> None:
    doc = compile_source_document(SPEC)
    m = work_order_map(doc)
    m.scopes[1].exhaustive = None

    assert "the document does not say whether all ways are listed" in m.render(doc)
    assert IntentMap.from_dict(m.to_dict()).scopes[1].exhaustive is None
    question = PermissionsQuestion(scopes=[m.scopes[1]])
    assert "signoff (principal User, resource WorkOrder)" in question.render()
    assert question.to_dict()["scopes"][0]["id"] == "s_signoff"


def test_render_lists_a_restriction_once_not_inside_each_slice() -> None:
    doc = compile_source_document(SPEC)
    ids = node_ids(doc)
    m = work_order_map(doc)
    m.slices.append(MapSlice("sl_signoff_2", "s_signoff", "a second way to sign off"))
    m.sentences = [s for s in m.sentences if s.node_id != ids["signoff:on hold"]] + [
        MapSentence(ids["signoff:on hold"], "condition", [], ["s_signoff"]),
        MapSentence(ids["signoff:inspector"], "condition", ["sl_signoff", "sl_signoff_2"]),
    ]
    m.sentences = [s for i, s in enumerate(m.sentences) if not (
        s.node_id == ids["signoff:inspector"] and s.slice_ids == ["sl_signoff"]
    )]

    text = m.render(doc)

    assert text.count(ids["signoff:on hold"]) == 1
    assert "and every restriction below" in text
    # The floor still joins the restriction into every slice of its scope.
    assert ids["signoff:on hold"] in m.slice_conditions("sl_signoff_2")


def test_named_objections_are_applied_to_the_map() -> None:
    doc = compile_source_document(SPEC)
    ids = node_ids(doc)
    known = {node.id for node in doc.nodes}
    m = work_order_map(doc)
    hold = ids["signoff:on hold"]

    assert m.apply_objection({"kind": "move_condition", "node_id": hold, "restricts_scope_ids": ["s_signoff"]}, known) == ""
    assert m.condition(hold).slice_ids == [] and m.restrictions("s_signoff") == [hold]
    assert m.apply_objection({"kind": "make_interpretation", "node_id": hold}, known) == ""
    assert hold in m.interpretation_ids() and m.condition(hold) is None
    assert m.apply_objection({"kind": "add_condition", "node_id": hold, "slice_ids": ["sl_signoff"]}, known) == ""
    assert m.condition(hold).slice_ids == ["sl_signoff"]
    assert m.apply_objection({"kind": "unmark_scope", "scope_id": "s_release"}, known) == ""
    assert m.scope_by_id["s_release"].exhaustive is None
    assert m.apply_objection({"kind": "drop_sentence", "node_id": ids["rule"]}, known) == ""
    assert ids["rule"] not in m.interpretation_ids()

    # Anything the map cannot apply on its own goes back to the mapper.
    assert m.apply_objection({"kind": "other", "detail": "split the slice"}, known) == "needs the mapper"
    assert "unknown slice" in m.apply_objection({"kind": "move_condition", "node_id": hold, "slice_ids": ["sl_x"]}, known)
    assert "unknown source node" in m.apply_objection({"kind": "drop_sentence", "node_id": "src.nope"}, known)
    assert "no slice or scope" in m.apply_objection({"kind": "move_condition", "node_id": hold}, known)


def test_slices_with_the_same_conditions_are_merged() -> None:
    doc = compile_source_document(SPEC)
    ids = node_ids(doc)
    m = work_order_map(doc)
    # The mapper split release into two "ways" that carry the same conditions.
    m.slices.append(MapSlice("sl_release_2", "s_release", "same conditions again"))
    for s in m.sentences:
        if "sl_release" in s.slice_ids:
            s.slice_ids = ["sl_release", "sl_release_2"]

    assert m.merge_duplicate_slices() == ["sl_release_2"]
    assert [sl.id for sl in m.scope_slices("s_release")] == ["sl_release"]
    assert m.condition(ids["release:inspector"]).slice_ids == ["sl_release"]
    assert m.structure_errors(doc, set()) == []
    # Slices with different conditions stay apart.
    assert m.merge_duplicate_slices() == []


@requires_cedar
def test_condition_atom_that_holds_for_every_request_fails_its_checks(tmp_path) -> None:
    from autocedar.grounding import symbolic_verify_atom

    schema = tmp_path / "schema.cedarschema"
    schema.write_text(SCHEMA)

    def checked(expr: str) -> list[str]:
        atom = condition_atom("src.x", "release", expr)
        symbolic_verify_atom(atom, str(schema), workdir=tmp_path)
        return [line for line in atom.symbolic_verification_log if line.startswith("match-broadness")]

    # As in the Haiku run: a field the schema does not declare, behind `has`,
    # makes the requirement vanish.
    vanished = checked("!(resource has frozen && resource.frozen) || resource.defectCount == 0")
    assert vanished[0].startswith("match-broadness: FAILED")
    assert checked("resource.defectCount == 0")[0].startswith("match-broadness: ok")
    # A sentence that only grants its scope says so with a literal `true`.
    assert checked("true")[0].startswith("match-broadness: ok (unconditional")
    assert checked("true || resource.defectCount == 0")[0].startswith("match-broadness: FAILED")


def _solved_except_on_hold(ids: dict[str, str]) -> list[PropertyAtom]:
    return [
        condition_atom(ids["release:inspector"], "release", CONDITIONS["inspector"]),
        condition_atom(ids["release:defect count"], "release", CONDITIONS["defect count"]),
        condition_atom(ids["signoff:inspector"], "signoff", CONDITIONS["inspector"]),
    ]


def test_drop_unsolved_removes_the_slice_that_needs_the_condition() -> None:
    doc = compile_source_document(SPEC)
    ids = node_ids(doc)
    imap = work_order_map(doc)

    dropped = imap.drop_unsolved(_solved_except_on_hold(ids))

    assert dropped == [{
        "node_id": ids["signoff:on hold"], "scope_id": "s_signoff",
        "effect": "slice removed", "slices": ["sl_signoff"],
    }]
    # Sign-off is now denied whole; release keeps its slice.
    assert [sl.id for sl in imap.slices] == ["sl_release"]
    assert imap.scope_by_id["s_signoff"].exhaustive is True
    assert imap.condition(ids["signoff:inspector"]) is None
    assert imap.status(_solved_except_on_hold(ids))["root_solved"] is True


def test_drop_unsolved_denies_a_scope_whose_restriction_is_unsolved() -> None:
    doc = compile_source_document(SPEC)
    ids = node_ids(doc)
    imap = work_order_map(doc)
    imap.scope_by_id["s_signoff"].exhaustive = False
    imap.condition(ids["signoff:on hold"]).slice_ids = []
    imap.condition(ids["signoff:on hold"]).restricts_scope_ids = ["s_signoff"]

    dropped = imap.drop_unsolved(_solved_except_on_hold(ids))

    assert [(d["node_id"], d["effect"]) for d in dropped] == [(ids["signoff:on hold"], "scope denied")]
    assert imap.scope_slices("s_signoff") == []
    assert imap.scope_by_id["s_signoff"].exhaustive is True
    assert imap.condition(ids["signoff:on hold"]) is None


def test_drop_unsolved_keeps_a_solved_map_unchanged() -> None:
    doc = compile_source_document(SPEC)
    ids = node_ids(doc)
    imap = work_order_map(doc)
    solved = _solved_except_on_hold(ids) + [
        condition_atom(ids["signoff:on hold"], "signoff", CONDITIONS["on hold"]),
    ]
    before = imap.to_dict()

    assert imap.drop_unsolved(solved) == []
    assert imap.to_dict() == before
