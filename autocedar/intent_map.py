"""The intent map: AutoCedar's task graph, after LEAP's AND-OR blueprint DAG.

LEAP keeps a proof plan as an AND-OR DAG of goals. AutoCedar keeps the policy
plan the same way:

- the root is the policy store for the requirements document;
- a scope is an OR node: the requests for one principal type, action and
  resource type, allowed when any one of its slices holds;
- a slice is an AND node: one way to be allowed, which holds only when all of
  its conditions hold;
- a condition is a requirement sentence, with edges to the slices it
  constrains and to the scopes it restricts as a whole;
- a leaf is an approved condition atom: the Cedar condition for one
  (condition, scope) pair.

Sentences that tell how to read the others are interpretation rules, given to
every model call. All other sentences carry no requirement.

The model proposes the map from the whole document; a reviewer approves it
before any atom is written. AutoCedar then calculates floors and ceilings from
the map and the approved conditions, so the model never writes a floor, and a
node counts as solved only when an approved atom grounds it.
"""

from __future__ import annotations

import json
import re
import subprocess
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Optional

from autocedar.atoms import PropertyAtom
from autocedar.cedar_text import policy_conditions
from autocedar.source_doc import SourceDocument, SourceNode, atom_source_ids


CONDITION = "condition"
INTERPRETATION = "interpretation"
_SAFE_ID = re.compile(r"[^a-z0-9_]+")


def safe_id(raw: str) -> str:
    """Lowercase identifier usable in file and check names."""
    return _SAFE_ID.sub("_", raw.strip().lower()).strip("_") or "x"


@dataclass
class MapScope:
    id: str
    action: str
    principal_type: str
    resource_type: str
    # True: the document lists every way to allow the scope; False: its ways
    # are examples. None: the document does not say, and the reviewer is asked.
    exhaustive: bool | None = True
    summary: str = ""


@dataclass
class MapSlice:
    id: str
    scope_id: str
    summary: str = ""


@dataclass
class MapSentence:
    node_id: str
    kind: str
    slice_ids: list[str] = field(default_factory=list)
    restricts_scope_ids: list[str] = field(default_factory=list)
    note: str = ""


@dataclass
class IntentMap:
    """The approved task graph for one requirements document."""

    scopes: list[MapScope] = field(default_factory=list)
    slices: list[MapSlice] = field(default_factory=list)
    sentences: list[MapSentence] = field(default_factory=list)
    # Set by the pipeline for reviewers: the rendered map, and the document as
    # numbered source nodes. Neither is saved with the map.
    review_text: str = ""
    outline: str = ""
    name: str = "intent_map"

    # -- (de)serialization ---------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        return {
            "scopes": [asdict(s) for s in self.scopes],
            "slices": [asdict(s) for s in self.slices],
            "sentences": [asdict(s) for s in self.sentences],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "IntentMap":
        return cls(
            scopes=[MapScope(**s) for s in data.get("scopes", [])],
            slices=[MapSlice(**s) for s in data.get("slices", [])],
            sentences=[MapSentence(**s) for s in data.get("sentences", [])],
        )

    # -- lookups -------------------------------------------------------------

    @property
    def scope_by_id(self) -> dict[str, MapScope]:
        return {s.id: s for s in self.scopes}

    @property
    def slice_by_id(self) -> dict[str, MapSlice]:
        return {s.id: s for s in self.slices}

    def conditions(self) -> list[MapSentence]:
        return [s for s in self.sentences if s.kind == CONDITION]

    def interpretation_ids(self) -> list[str]:
        return [s.node_id for s in self.sentences if s.kind == INTERPRETATION]

    def condition(self, node_id: str) -> Optional[MapSentence]:
        return next((s for s in self.conditions() if s.node_id == node_id), None)

    def condition_node_ids(self, doc: SourceDocument) -> list[str]:
        """Condition nodes in document order."""
        order = {node.id: node.ordinal for node in doc.nodes}
        ids = [s.node_id for s in self.conditions() if s.node_id in order]
        return sorted(dict.fromkeys(ids), key=lambda node_id: order[node_id])

    def scopes_for_node(self, node_id: str) -> list[MapScope]:
        sentence = self.condition(node_id)
        if sentence is None:
            return []
        slices = self.slice_by_id
        scope_ids = [slices[s].scope_id for s in sentence.slice_ids if s in slices]
        scope_ids += [s for s in sentence.restricts_scope_ids if self.needs_restriction_atom(s)]
        by_id = self.scope_by_id
        return [by_id[s] for s in dict.fromkeys(scope_ids) if s in by_id]

    def needs_restriction_atom(self, scope_id: str) -> bool:
        """Whether a restriction on this scope needs its own atom.

        A scope that lists every way to allow it and has none is denied whole
        (its ceiling denies every request), so a sentence that forbids it, such
        as "the system will not update the legacy data", adds nothing to encode.
        """
        scope = self.scope_by_id.get(scope_id)
        return not (scope is not None and scope.exhaustive is True and not self.scope_slices(scope_id))

    def slice_conditions(self, slice_id: str) -> list[str]:
        """Condition node ids of a slice, including restrictions on its scope."""
        sl = self.slice_by_id.get(slice_id)
        if sl is None:
            return []
        return [
            s.node_id
            for s in self.conditions()
            if slice_id in s.slice_ids or sl.scope_id in s.restricts_scope_ids
        ]

    def restrictions(self, scope_id: str) -> list[str]:
        return [s.node_id for s in self.conditions() if scope_id in s.restricts_scope_ids]

    def scope_slices(self, scope_id: str) -> list[MapSlice]:
        return [s for s in self.slices if s.scope_id == scope_id]

    # -- step 2: structure check --------------------------------------------

    def structure_errors(
        self,
        doc: SourceDocument,
        schema_triples: set[tuple[str, str, str]],
    ) -> list[str]:
        """Mechanical checks a map must pass before anyone reviews it."""
        errors: list[str] = []
        node_ids = {node.id for node in doc.nodes}
        if not self.scopes:
            errors.append("The map has no scope: no action is allowed or restricted.")
        scope_ids = [s.id for s in self.scopes]
        for dup in sorted({s for s in scope_ids if scope_ids.count(s) > 1}):
            errors.append(f"Scope id {dup!r} is used more than once.")
        triples = [(s.principal_type, _bare_action(s.action), s.resource_type) for s in self.scopes]
        for dup in sorted({t for t in triples if triples.count(t) > 1}):
            errors.append(f"Two scopes cover the same request environment {dup}.")
        for scope in self.scopes:
            triple = (scope.principal_type, _bare_action(scope.action), scope.resource_type)
            if schema_triples and triple not in schema_triples:
                errors.append(
                    f"Scope {scope.id!r}: the schema has no action {triple[1]!r} for "
                    f"principal {triple[0]!r} and resource {triple[2]!r}.",
                )
        slice_ids = [s.id for s in self.slices]
        for dup in sorted({s for s in slice_ids if slice_ids.count(s) > 1}):
            errors.append(f"Slice id {dup!r} is used more than once.")
        for sl in self.slices:
            if sl.scope_id not in scope_ids:
                errors.append(f"Slice {sl.id!r} points to unknown scope {sl.scope_id!r}.")
            elif not self.slice_conditions(sl.id):
                errors.append(f"Slice {sl.id!r} has no condition.")
        seen: set[str] = set()
        for sentence in self.sentences:
            if sentence.node_id not in node_ids:
                errors.append(f"Unknown source node {sentence.node_id!r}.")
            if sentence.node_id in seen:
                errors.append(f"Source node {sentence.node_id!r} is classified more than once.")
            seen.add(sentence.node_id)
            if sentence.kind not in (CONDITION, INTERPRETATION):
                errors.append(f"Source node {sentence.node_id!r} has unknown kind {sentence.kind!r}.")
                continue
            if sentence.kind != CONDITION:
                continue
            if not sentence.slice_ids and not sentence.restricts_scope_ids:
                errors.append(f"Condition {sentence.node_id!r} constrains no slice or scope.")
            for sid in sentence.slice_ids:
                if sid not in slice_ids:
                    errors.append(f"Condition {sentence.node_id!r} points to unknown slice {sid!r}.")
            for sid in sentence.restricts_scope_ids:
                if sid not in scope_ids:
                    errors.append(f"Condition {sentence.node_id!r} points to unknown scope {sid!r}.")
        if _has_cycle(self._edges()):
            errors.append("The map has a cycle.")
        return errors

    def missing_actions(self, schema_triples: set[tuple[str, str, str]]) -> list[tuple[str, str, str]]:
        """(principal type, action, resource type) of each scope the schema does not declare."""
        missing: list[tuple[str, str, str]] = []
        for scope in self.scopes:
            triple = (scope.principal_type, _bare_action(scope.action), scope.resource_type)
            if schema_triples and triple not in schema_triples and triple not in missing:
                missing.append(triple)
        return missing

    def drop_scopes(self, triples: list[tuple[str, str, str]]) -> list[str]:
        """Remove the scopes for these requests, their slices, and conditions left without a scope.

        Returns the node ids of the conditions that left the map.
        """
        gone = {
            s.id for s in self.scopes
            if (s.principal_type, _bare_action(s.action), s.resource_type) in triples
        }
        gone_slices = {sl.id for sl in self.slices if sl.scope_id in gone}
        self.scopes = [s for s in self.scopes if s.id not in gone]
        self.slices = [sl for sl in self.slices if sl.id not in gone_slices]
        dropped: list[str] = []
        kept: list[MapSentence] = []
        for sentence in self.sentences:
            if sentence.kind == CONDITION:
                sentence.slice_ids = [i for i in sentence.slice_ids if i not in gone_slices]
                sentence.restricts_scope_ids = [i for i in sentence.restricts_scope_ids if i not in gone]
                if not sentence.slice_ids and not sentence.restricts_scope_ids:
                    dropped.append(sentence.node_id)
                    continue
            kept.append(sentence)
        self.sentences = kept
        return dropped

    def drop_unsolved(
        self,
        approved: Iterable[PropertyAtom],
        no_condition: Iterable[str] = (),
    ) -> list[dict[str, Any]]:
        """Remove each condition that has no approved atom, in the direction that allows less.

        Noisy mode uses this instead of stopping. A slice that needs an unsolved
        condition leaves the map, so nothing is allowed without that condition.
        A scope with an unsolved restriction is denied whole: it loses its
        slices and is marked complete, so its ceiling denies every request.
        A sentence in ``no_condition`` was judged to add no condition at all
        (its only encoding, `when { true }`, was rejected as not a
        requirement), so it leaves the map without taking its slices along;
        a slice it leaves with no condition is removed.
        Returns one record per dropped (condition, scope) pair.
        """
        grounded = self.grounding(list(approved))
        no_condition = set(no_condition)
        dropped: list[dict[str, Any]] = []
        gone_slices: set[str] = set()
        denied: set[str] = set()
        slice_scope = {sl.id: sl.scope_id for sl in self.slices}
        for sentence in self.conditions():
            for scope in self.scopes_for_node(sentence.node_id):
                if (sentence.node_id, scope.id) in grounded:
                    continue
                if sentence.node_id in no_condition:
                    dropped.append({
                        "node_id": sentence.node_id,
                        "scope_id": scope.id,
                        "effect": "not a requirement; left the map",
                        "slices": [],
                    })
                    continue
                restricts = scope.id in sentence.restricts_scope_ids
                slices = [i for i in sentence.slice_ids if slice_scope.get(i) == scope.id]
                gone_slices.update(slices)
                if restricts:
                    denied.add(scope.id)
                dropped.append({
                    "node_id": sentence.node_id,
                    "scope_id": scope.id,
                    "effect": "scope denied" if restricts else "slice removed",
                    "slices": slices,
                })
        for scope in self.scopes:
            if scope.id in denied:
                gone_slices.update(sl.id for sl in self.scope_slices(scope.id))
                scope.exhaustive = True
        self.sentences = [
            s for s in self.sentences if not (s.kind == CONDITION and s.node_id in no_condition)
        ]
        # A slice whose only conditions were not requirements would allow its
        # whole scope; it goes too.
        gone_slices.update(sl.id for sl in self.slices if not self.slice_conditions(sl.id))
        removed_scopes = {sl.scope_id for sl in self.slices if sl.id in gone_slices}
        self.slices = [sl for sl in self.slices if sl.id not in gone_slices]
        for scope in self.scopes:
            # A scope that lost every way to be allowed is denied, not left open.
            if scope.id in removed_scopes and not self.scope_slices(scope.id):
                scope.exhaustive = True
        kept: list[MapSentence] = []
        for sentence in self.sentences:
            if sentence.kind == CONDITION:
                sentence.slice_ids = [i for i in sentence.slice_ids if i not in gone_slices]
                sentence.restricts_scope_ids = [i for i in sentence.restricts_scope_ids if i not in denied]
                if not sentence.slice_ids and not sentence.restricts_scope_ids:
                    continue
            kept.append(sentence)
        self.sentences = kept
        return dropped

    def _edges(self) -> dict[str, list[str]]:
        """Child-to-parent edges: condition -> slice/scope -> root."""
        edges: dict[str, list[str]] = {}
        for scope in self.scopes:
            edges.setdefault(f"scope:{scope.id}", []).append("root")
        for sl in self.slices:
            edges.setdefault(f"slice:{sl.id}", []).append(f"scope:{sl.scope_id}")
        for s in self.conditions():
            node = f"condition:{s.node_id}"
            edges.setdefault(node, []).extend(f"slice:{x}" for x in s.slice_ids)
            edges.setdefault(node, []).extend(f"scope:{x}" for x in s.restricts_scope_ids)
        return edges

    # -- step 5: status ------------------------------------------------------

    def grounding(self, approved: Iterable[PropertyAtom]) -> dict[tuple[str, str], PropertyAtom]:
        """Approved condition atom for each (condition node, scope) pair."""
        out: dict[tuple[str, str], PropertyAtom] = {}
        for atom in approved:
            if atom.constraint_type != CONDITION:
                continue
            for node_id in atom_source_ids(atom):
                for scope in self.scopes_for_node(node_id):
                    if atom_fits_scope(atom, scope):
                        out.setdefault((node_id, scope.id), atom)
        return out

    def unsolved_scopes(self, node_id: str, approved: Iterable[PropertyAtom]) -> list[MapScope]:
        grounded = self.grounding(approved)
        return [s for s in self.scopes_for_node(node_id) if (node_id, s.id) not in grounded]

    def status(self, approved: Iterable[PropertyAtom]) -> dict[str, Any]:
        """Solved state of every node, from the leaves up to the root."""
        grounded = self.grounding(list(approved))
        conditions = {
            s.node_id: {
                scope.id: (s.node_id, scope.id) in grounded
                for scope in self.scopes_for_node(s.node_id)
            }
            for s in self.conditions()
        }
        slices = {
            sl.id: all(conditions.get(n, {}).get(sl.scope_id, False) for n in self.slice_conditions(sl.id))
            for sl in self.slices
        }
        scopes = {
            scope.id: all(slices[sl.id] for sl in self.scope_slices(scope.id))
            and (
                not self.needs_restriction_atom(scope.id)
                or all(conditions.get(n, {}).get(scope.id, False) for n in self.restrictions(scope.id))
            )
            for scope in self.scopes
        }
        blocking = sorted(
            {node_id for node_id, by_scope in conditions.items() if not all(by_scope.values())},
        )
        return {
            "root_solved": all(scopes.values()) and bool(scopes),
            "scopes": scopes,
            "slices": slices,
            "conditions": conditions,
            "blocking_conditions": blocking,
        }

    # -- review --------------------------------------------------------------

    def merge_duplicate_slices(self) -> list[str]:
        """Merge slices of one scope that have the same conditions.

        Two ways to be allowed with the same conditions are one way: their
        floors are the same policy. Returns the ids of the slices merged away.
        """
        merged: list[str] = []
        for scope in self.scopes:
            kept: dict[frozenset[str], str] = {}
            for sl in self.scope_slices(scope.id):
                own = frozenset(s.node_id for s in self.conditions() if sl.id in s.slice_ids)
                if own in kept:
                    merged.append(sl.id)
                    for sentence in self.sentences:
                        if sl.id in sentence.slice_ids:
                            sentence.slice_ids = list(dict.fromkeys(
                                kept[own] if i == sl.id else i for i in sentence.slice_ids
                            ))
                else:
                    kept[own] = sl.id
        self.slices = [sl for sl in self.slices if sl.id not in set(merged)]
        return merged

    # -- objections a reviewer names -------------------------------------------

    def apply_objection(self, objection: dict[str, Any], node_ids: set[str]) -> str:
        """Apply one named objection to the map.

        Returns "" when applied, or why it was not: an objection of kind
        "other", or one that names an unknown node, slice, or scope, goes back
        to the mapper instead.
        """
        kind = objection.get("kind", "other")
        node_id = objection.get("node_id", "")
        slice_ids = list(objection.get("slice_ids") or [])
        scope_ids = list(objection.get("restricts_scope_ids") or [])
        sentence = next((s for s in self.sentences if s.node_id == node_id), None)
        if kind == "unmark_scope":
            scope = self.scope_by_id.get(objection.get("scope_id", ""))
            if scope is None:
                return f"unknown scope {objection.get('scope_id')!r}"
            scope.exhaustive = None
            return ""
        if kind not in {"move_condition", "add_condition", "make_interpretation", "drop_sentence"}:
            return "needs the mapper"
        if node_id not in node_ids:
            return f"unknown source node {node_id!r}"
        if kind == "drop_sentence":
            if sentence is None:
                return f"source node {node_id!r} is not in the map"
            self.sentences.remove(sentence)
            return ""
        if kind == "make_interpretation":
            slice_ids, scope_ids, new_kind = [], [], INTERPRETATION
        else:
            unknown = [i for i in slice_ids if i not in self.slice_by_id]
            unknown += [i for i in scope_ids if i not in self.scope_by_id]
            if unknown:
                return f"unknown slice or scope {unknown}"
            if not slice_ids and not scope_ids:
                return "no slice or scope given"
            new_kind = CONDITION
        if sentence is None:
            self.sentences.append(MapSentence(node_id, new_kind, slice_ids, scope_ids))
        else:
            sentence.kind, sentence.slice_ids, sentence.restricts_scope_ids = new_kind, slice_ids, scope_ids
        return ""

    def render(self, doc: SourceDocument) -> str:
        """Plain-text map for reviewers: every node with its source sentence."""
        text = {node.id: node.text for node in doc.nodes}
        lines = ["INTENT MAP", ""]
        for scope in self.scopes:
            listed = {
                True: "all ways to allow it are listed",
                False: "the listed ways are examples",
                None: "the document does not say whether all ways are listed",
            }[scope.exhaustive]
            lines.append(
                f"Scope {scope.id}: principal {scope.principal_type}, action "
                f"{_bare_action(scope.action)}, resource {scope.resource_type} ({listed})",
            )
            if scope.summary:
                lines.append(f"  {scope.summary}")
            restrictions = self.restrictions(scope.id)
            also = " and every restriction below" if restrictions else ""
            for sl in self.scope_slices(scope.id):
                lines.append(f"  Slice {sl.id}: {sl.summary} (all of these must hold{also})")
                # The slice's own conditions; restrictions are listed once below.
                for s in self.conditions():
                    if sl.id in s.slice_ids:
                        lines.append(f"    - [{s.node_id}] {text.get(s.node_id, '?')}")
            if restrictions:
                lines.append("  Restrictions on every request of this scope:")
                lines.extend(f"    - [{n}] {text.get(n, '?')}" for n in restrictions)
            lines.append("")
        rules = self.interpretation_ids()
        lines.append("Rules for interpretation (context for every step):")
        lines.extend(f"  - [{n}] {text.get(n, '?')}" for n in rules)
        if not rules:
            lines.append("  - none")
        listed = {s.node_id for s in self.sentences}
        unlisted = [node for node in doc.nodes if node.id not in listed]
        lines.append("")
        lines.append(f"Sentences with no requirement ({len(unlisted)}):")
        lines.extend(f"  - [{node.id}] {node.text}" for node in unlisted)
        return "\n".join(lines)


@dataclass
class PermissionsQuestion:
    """Asks whether the document lists every permission for the scopes it leaves unmarked.

    Reviewed like an atom: approve means yes, so each scope's ceiling equals
    its floors; reject means no, the listed permissions are examples.
    """

    scopes: list[MapScope]
    outline: str = ""
    name: str = "permissions_complete"

    def render(self) -> str:
        lines = [
            "IS THE LIST OF PERMISSIONS COMPLETE?",
            "",
            "The requirements do not say whether they list every way to allow these actions:",
        ]
        lines += [
            f"  - {_bare_action(s.action)} (principal {s.principal_type}, resource {s.resource_type})"
            for s in self.scopes
        ]
        lines += [
            "",
            "Approve: yes, the list is complete; any request it does not allow is denied.",
            "Reject: no, the listed permissions are examples; more requests may be allowed.",
        ]
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {"question": self.name, "scopes": [asdict(s) for s in self.scopes]}


# ---------------------------------------------------------------------------
# Step 3: context for one condition, taken from the map's edges.
# ---------------------------------------------------------------------------

CONDITION_PACKET_TAG = "autocedar_condition_packet"


@dataclass
class ConditionPacket:
    """Everything the model needs to encode one condition, drawn from the map."""

    id: str
    kind: str
    focus_node_ids: list[str]
    text: str
    scope_ids: list[str]
    # Sentences the call received as context: slice siblings and rules.
    related_nodes: list[SourceNode] = field(default_factory=list)

    def to_prompt_text(self, *, include_review_context: bool = False) -> str:
        _ = include_review_context
        return self.text

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "focus_node_ids": list(self.focus_node_ids),
            "scope_ids": list(self.scope_ids),
            "related_node_ids": [node.id for node in self.related_nodes],
            "text": self.text,
        }


def is_condition_packet(text: str) -> bool:
    return f"<{CONDITION_PACKET_TAG}" in text


def build_condition_packet(
    doc: SourceDocument,
    intent_map: IntentMap,
    node: SourceNode,
    approved: list[PropertyAtom],
    step: int,
) -> ConditionPacket:
    by_id = doc.by_id
    grounded = intent_map.grounding(approved)
    scopes = intent_map.scopes_for_node(node.id)
    sentence = intent_map.condition(node.id)
    related: list[str] = []
    lines = [
        f'<{CONDITION_PACKET_TAG} id="condition.{node.ordinal:04d}.step{step:04d}">',
        "Requirement to encode:",
        _format_node(node),
        "",
        "Write one condition atom for each scope below. AutoCedar joins the "
        "conditions of a slice with AND and the slices of a scope with OR, so "
        "encode only what this requirement says.",
    ]
    for scope in scopes:
        listed = "every way to allow it is listed" if scope.exhaustive else "the listed ways are examples"
        lines += [
            "",
            f"Scope {scope.id}: principal {scope.principal_type}, action "
            f"{_bare_action(scope.action)}, resource {scope.resource_type} ({listed}).",
        ]
        if sentence is not None and scope.id in sentence.restricts_scope_ids:
            lines.append("  This requirement restricts every request of this scope.")
        for sl in intent_map.scope_slices(scope.id):
            members = intent_map.slice_conditions(sl.id)
            if node.id not in members:
                continue
            lines.append(f"  It is a condition of slice {sl.id}: {sl.summary}")
            others = [n for n in members if n != node.id]
            related.extend(others)
            lines.append("  The other conditions of this slice (encoded separately):")
            lines.extend(f"    {_format_node(by_id[n])}" for n in others if n in by_id)
            if not others:
                lines.append("    - none")
        approved_here = {
            atom.name: atom for (node_id, scope_id), atom in grounded.items()
            if scope_id == scope.id and node_id != node.id
        }
        lines.append("  Approved condition atoms of this scope:")
        lines.extend(
            f"    - {atom.name}: {atom.plain_english_summary} | {' '.join(atom.reference_cedar.split())}"
            for atom in approved_here.values()
        )
        if not approved_here:
            lines.append("    - none yet")
    rules = intent_map.interpretation_ids()
    related.extend(rules)
    lines += ["", "Rules for interpretation (apply them to every requirement):"]
    lines.extend(f"  {_format_node(by_id[n])}" for n in rules if n in by_id)
    if not rules:
        lines.append("  - none")
    lines.append(f"</{CONDITION_PACKET_TAG}>")
    return ConditionPacket(
        id=f"condition.{node.ordinal:04d}.step{step:04d}",
        kind="condition",
        focus_node_ids=[node.id],
        text="\n".join(lines) + "\n",
        scope_ids=[s.id for s in scopes],
        related_nodes=[by_id[n] for n in dict.fromkeys(related) if n in by_id],
    )


def _format_node(node: SourceNode) -> str:
    section = " / ".join(node.heading_path) if node.heading_path else "root"
    return f"[source_id: {node.id}; section: {section}] {node.text}"


# ---------------------------------------------------------------------------
# Condition atoms: shape and scope.
# ---------------------------------------------------------------------------

def atom_fits_scope(atom: PropertyAtom, scope: MapScope) -> bool:
    return (
        _bare_action(atom.action) == _bare_action(scope.action)
        and list(atom.principal_types) == [scope.principal_type]
        and list(atom.resource_types) == [scope.resource_type]
    )


def condition_atom_issue(intent_map: IntentMap, atom: PropertyAtom, node_id: str) -> str:
    """Why a proposed atom cannot ground this condition node, or ''."""
    scopes = intent_map.scopes_for_node(node_id)
    if atom.constraint_type != CONDITION:
        return (
            f"In the intent map, AutoCedar calculates floors and ceilings itself; "
            f"propose a 'condition' atom, not a {atom.constraint_type!r} atom."
        )
    if not any(atom_fits_scope(atom, scope) for scope in scopes):
        wanted = "; ".join(
            f"{s.principal_type} / {_bare_action(s.action)} / {s.resource_type}" for s in scopes
        )
        return (
            "The atom's action and types match no scope of this requirement. "
            f"Use one of: {wanted}."
        )
    return ""


def condition_shape_issue(reference_cedar: str, atom: PropertyAtom, cedar_path: str) -> str:
    """A condition atom must be one permit whose scope matches the atom's types."""
    try:
        policy = _single_policy_json(reference_cedar, cedar_path)
    except ValueError as exc:
        return str(exc)
    if policy.get("effect") != "permit":
        return "A condition atom must be a permit policy, not a forbid policy."
    if not policy.get("conditions"):
        return "A condition atom must state its condition in a when or unless clause."
    action = policy.get("action", {})
    if action.get("op") != "==" or action.get("entity", {}).get("id") != _bare_action(atom.action):
        return f"The policy's action must be exactly Action::\"{_bare_action(atom.action)}\"."
    for var, types in (("principal", atom.principal_types), ("resource", atom.resource_types)):
        clause = policy.get(var, {})
        if clause.get("op") == "All":
            continue
        if clause.get("op") == "is" and "in" not in clause and [clause.get("entity_type")] == list(types):
            continue
        return f"The policy's {var} scope must be `{var}` or `{var} is {types[0] if types else '?'}`."
    return ""


# ---------------------------------------------------------------------------
# Step 4: floors and ceilings calculated from the map.
# ---------------------------------------------------------------------------

# Log line for a condition atom that can raise a runtime error alone but not
# after the other conditions of its slice.
GUARDED_BY_SLICE = "never-errors: ok (guarded by the earlier conditions of its slice)"


def needs_slice_guard(atom: PropertyAtom) -> bool:
    return GUARDED_BY_SLICE in (atom.symbolic_verification_log or [])


def derive_boundary_atoms(
    intent_map: IntentMap,
    approved: list[PropertyAtom],
    *,
    cedar_path: str,
) -> tuple[list[PropertyAtom], list[str]]:
    """Floors and ceilings for every scope, from the approved condition atoms.

    A slice floor is one permit whose conditions are the AND of the slice's
    conditions. A scope's floors are its slice floors (their OR). When a scope
    lists every way to allow it, its ceiling is the same set of permits, so the
    plan is exact; otherwise each whole-scope restriction becomes a ceiling.
    """
    grounded = intent_map.grounding(approved)
    derived: list[PropertyAtom] = []
    issues: list[str] = []
    order = {s.node_id: i for i, s in enumerate(intent_map.sentences)}
    for scope in intent_map.scopes:
        floors: list[str] = []
        for sl in intent_map.scope_slices(scope.id):
            node_ids = sorted(intent_map.slice_conditions(sl.id), key=lambda n: order.get(n, 0))
            missing = [n for n in node_ids if (n, scope.id) not in grounded]
            if missing:
                issues.append(f"Slice {sl.id} of scope {scope.id} has no approved atom for {missing}.")
                continue
            # Cedar's && stops at the first false conjunct, so an atom that is
            # only safe after its slice's other conditions goes last.
            atoms = sorted((grounded[(n, scope.id)] for n in node_ids), key=needs_slice_guard)
            floor = merge_conditions(scope, atoms, cedar_path=cedar_path)
            floors.append(floor)
            derived.append(_derived_atom(
                name=f"floor__{safe_id(scope.id)}__{safe_id(sl.id)}",
                kind="floor",
                scope=scope,
                cedar=floor,
                summary=f"Requests in slice '{sl.summary or sl.id}' must be allowed.",
                atoms=atoms,
            ))
        if scope.exhaustive:
            ceiling = "\n\n".join(floors) if floors else _deny_all(scope)
            derived.append(_derived_atom(
                name=f"ceiling__{safe_id(scope.id)}",
                kind="ceiling",
                scope=scope,
                cedar=ceiling,
                summary=(
                    "Only requests in one of this scope's slices may be allowed."
                    if floors else "No request of this scope may be allowed."
                ),
                atoms=[grounded[k] for k in grounded if k[1] == scope.id],
            ))
            continue
        for node_id in intent_map.restrictions(scope.id):
            atom = grounded.get((node_id, scope.id))
            if atom is None:
                continue
            derived.append(_derived_atom(
                name=f"ceiling__{safe_id(scope.id)}__{safe_id(node_id)}",
                kind="ceiling",
                scope=scope,
                cedar=merge_conditions(scope, [atom], cedar_path=cedar_path),
                summary=atom.plain_english_summary,
                atoms=[atom],
            ))
    return derived, issues


def merge_conditions(scope: MapScope, atoms: list[PropertyAtom], *, cedar_path: str) -> str:
    """One permit for the scope whose conditions are all of the atoms' conditions.

    Each atom's when and unless clauses are kept as written and in order, and
    Cedar joins the clauses of a policy with &&. The permit is built as text:
    Cedar's JSON reader stops at 128 levels of nesting, which a long chain of
    || or && in one atom can pass.
    """
    clauses: list[str] = []
    for atom in atoms:
        _single_policy_json(atom.reference_cedar, cedar_path)  # one policy, and it parses
        clauses.append(policy_conditions(atom.reference_cedar))
    head = (
        f"permit (\n  principal is {scope.principal_type},\n"
        f"  action == Action::\"{_bare_action(scope.action)}\",\n"
        f"  resource is {scope.resource_type}\n)"
    )
    return head + "".join(f"\n{clause}" for clause in clauses if clause) + ";"


def _derived_atom(*, name, kind, scope, cedar, summary, atoms) -> PropertyAtom:
    sources = list(dict.fromkeys(i for a in atoms for i in atom_source_ids(a)))
    return PropertyAtom(
        name=name,
        rationale="Calculated from the intent map and its approved condition atoms.",
        plain_english_summary=summary,
        source_excerpt=" ".join(f"[source_id: {s}]" for s in sources),
        constraint_type=kind,
        action=_bare_action(scope.action),
        principal_types=[scope.principal_type],
        resource_types=[scope.resource_type],
        reference_cedar=cedar,
        symbolic_verified=True,
    )


def _deny_all(scope: MapScope) -> str:
    return (
        f"permit (principal is {scope.principal_type}, action == Action::\""
        f"{_bare_action(scope.action)}\", resource is {scope.resource_type}) when {{ false }};"
    )


# ---------------------------------------------------------------------------
# Schema and Cedar helpers.
# ---------------------------------------------------------------------------

def schema_triples(schema_text: str, *, cedar_path: str) -> set[tuple[str, str, str]]:
    """(principal type, action, resource type) for every action in the schema."""
    data = json.loads(_cedar(
        cedar_path,
        ["translate-schema", "--direction", "cedar-to-json"],
        schema_text,
        input_flag="--schema",
    ))
    triples: set[tuple[str, str, str]] = set()
    for namespace, body in data.items():
        prefix = f"{namespace}::" if namespace else ""
        for action, spec in (body.get("actions") or {}).items():
            applies = spec.get("appliesTo") or {}
            for principal in applies.get("principalTypes") or []:
                for resource in applies.get("resourceTypes") or []:
                    triples.add((prefix + principal, action, prefix + resource))
                    triples.add((principal, action, resource))
    return triples


def schema_declarations(schema_text: str, *, cedar_path: str) -> set[str]:
    """Every entity type and action the schema declares, namespace-qualified."""
    data = json.loads(_cedar(
        cedar_path,
        ["translate-schema", "--direction", "cedar-to-json"],
        schema_text,
        input_flag="--schema",
    ))
    names: set[str] = set()
    for namespace, body in data.items():
        prefix = f"{namespace}::" if namespace else ""
        names.update(f"{prefix}{name}" for name in (body.get("entityTypes") or {}))
        names.update(f'{prefix}Action::"{name}"' for name in (body.get("actions") or {}))
    return names


def describe_schema_actions(triples: set[tuple[str, str, str]]) -> str:
    rows = sorted({f"- action {a}: principal {p}, resource {r}" for p, a, r in triples if "::" not in p})
    return "\n".join(rows) or "- none"


def _bare_action(action: str) -> str:
    action = action.strip()
    match = re.fullmatch(r'(?:[A-Za-z_][A-Za-z0-9_]*::)*Action::"(.*)"', action)
    return match.group(1) if match else action


def _single_policy_json(cedar_text: str, cedar_path: str) -> dict[str, Any]:
    try:
        data = json.loads(_cedar(cedar_path, ["translate-policy", "--direction", "cedar-to-json"], cedar_text))
    except (json.JSONDecodeError, RuntimeError) as exc:
        raise ValueError(f"The policy does not parse: {exc}") from exc
    policies = data.get("staticPolicies") or {}
    if data.get("templates") or len(policies) != 1:
        raise ValueError(f"A condition atom must be exactly one policy; found {len(policies)}.")
    return next(iter(policies.values()))


def _cedar(cedar_path: str, args: list[str], stdin_text: str, *, input_flag: str = "--policies") -> str:
    with tempfile.TemporaryDirectory(prefix="autocedar_map_") as tmp:
        path = Path(tmp) / "input"
        path.write_text(stdin_text)
        result = subprocess.run(
            [cedar_path, *args, input_flag, str(path)],
            capture_output=True, text=True, timeout=30,
        )
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout).strip()[:600])
    return result.stdout


def _has_cycle(edges: dict[str, list[str]]) -> bool:
    state: dict[str, int] = {}

    def visit(node: str) -> bool:
        if state.get(node) == 1:
            return True
        if state.get(node) == 2:
            return False
        state[node] = 1
        if any(visit(parent) for parent in edges.get(node, [])):
            return True
        state[node] = 2
        return False

    return any(visit(node) for node in list(edges))


def map_graph(intent_map: IntentMap) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    """Nodes and typed edges of the map, for the session's DAG artifact."""
    nodes: list[dict[str, Any]] = [{"id": "map:root", "kind": "policy_store"}]
    edges: list[dict[str, str]] = []
    for scope in intent_map.scopes:
        nodes.append({"id": f"scope:{scope.id}", "kind": "scope", **asdict(scope)})
        edges.append({"source": f"scope:{scope.id}", "target": "map:root", "type": "or_child_of"})
    for sl in intent_map.slices:
        nodes.append({"id": f"slice:{sl.id}", "kind": "slice", **asdict(sl)})
        edges.append({"source": f"slice:{sl.id}", "target": f"scope:{sl.scope_id}", "type": "or_alternative_of"})
    for s in intent_map.sentences:
        if s.kind == INTERPRETATION:
            edges.append({"source": s.node_id, "target": "map:root", "type": "interprets"})
            continue
        for sid in s.slice_ids:
            edges.append({"source": s.node_id, "target": f"slice:{sid}", "type": "and_condition_of"})
        for sid in s.restricts_scope_ids:
            edges.append({"source": s.node_id, "target": f"scope:{sid}", "type": "restricts"})
    return nodes, edges
