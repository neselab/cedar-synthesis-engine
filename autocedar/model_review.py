"""Atom review by the model when no person reviews (``--model-review``).

Batch runs used to approve any atom whose Cedar passed the symbolic checks, so
an atom that misread its requirement, for example by attaching it to the wrong
action, entered the target unexamined. The model reviewer instead judges each
atom against the full requirements document and rejects misreadings with a
reason, which the pipeline's repair planner then acts on.

Model review is not human approval: every decision it returns leaves
``intent_acknowledged_by_user`` false and records ``review_channel: model``.
"""

from __future__ import annotations

from typing import Any

from autocedar.atoms import PropertyAtom
from autocedar.corpus import AtomDecision
from autocedar.intent_map import IntentMap, PermissionsQuestion


class ModelReviewer:
    """Atom reviewer that asks the model whether each atom matches the requirements."""

    def __init__(self, llm: Any, spec_text: str) -> None:
        self.llm = llm
        self.spec_text = spec_text
        self.schema_text = ""
        self.approved: list[PropertyAtom] = []

    def schema_ready(self, schema_text: str) -> None:
        self.schema_text = schema_text

    def __call__(self, atom: Any) -> AtomDecision:
        # Cedar that fails the checks cannot enter the target whatever it means.
        if isinstance(atom, PropertyAtom) and not atom.symbolic_verified:
            log = atom.symbolic_verification_log or []
            failed = [str(line) for line in log if "FAILED" in str(line)] or [str(line) for line in log[:3]]
            return AtomDecision(
                atom_name=atom.name,
                action="reject",
                reason="Symbolic verification failed; the atom cannot enter the target. "
                + " ".join(failed),
                intent_acknowledged_by_user=False,
                symbolic_verified=False,
                edit_delta={"review_channel": "model"},
            )

        if isinstance(atom, IntentMap):
            review = self.llm.review_intent_map(
                intent_map=atom,
                outline=atom.outline or self.spec_text,
            )
        elif isinstance(atom, PermissionsQuestion):
            review = self.llm.answer_permissions_question(
                question=atom,
                outline=atom.outline or self.spec_text,
            )
        else:
            review = self.llm.review_atom_against_requirements(
                atom=atom,
                spec_text=self.spec_text,
                schema_text=self.schema_text,
                approved_atoms=self.approved,
            )
        delta = {"review_channel": "model", "model_review": review.reason}
        if review.decision == "approve":
            if isinstance(atom, PropertyAtom):
                self.approved.append(atom)
            return AtomDecision(
                atom_name=getattr(atom, "name", "?"),
                action="approve",
                intent_acknowledged_by_user=False,
                symbolic_verified=getattr(atom, "symbolic_verified", False),
                edit_delta=delta,
            )
        return AtomDecision(
            atom_name=getattr(atom, "name", "?"),
            action="reject",
            reason=f"Model review: {review.reason}",
            intent_acknowledged_by_user=False,
            symbolic_verified=getattr(atom, "symbolic_verified", False),
            edit_delta=delta,
        )
