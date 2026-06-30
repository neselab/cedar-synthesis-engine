"""Hand-authored verification plan for realworld/causal_predecessor_chain.

Tests the canonical "action B requires action A to have been previously
permitted" pattern, encoded with a host-supplied attestation record on
the request context. The chain is `prepare → submit → approve`, and
`approve` additionally enforces separation of duties (the submitter
cannot also approve).

Exercises:
- Optional record-typed context attribute (`predecessorAuthorized?`)
- `has`-guarded reads on the optional attribute (§8.3)
- String equality on a discriminator field (`actionType`)
- Cross-field constraint (`actor != principal`) enforcing SoD

3 ceilings + 3 floors + 3 liveness = 9 checks.
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # ── Safety ceilings (one per action) ─────────────────────────────
        {
            "name": "prepare_safety",
            "description": "prepare permitted for any user (root of chain)",
            "type": "implies",
            "principal_type": "User",
            "action": "Action::\"prepare\"",
            "resource_type": "Document",
            "reference_path": os.path.join(REFS, "prepare_safety.cedar"),
        },
        {
            "name": "submit_safety",
            "description": "submit permitted only when predecessorAuthorized is present AND actionType == 'prepare'",
            "type": "implies",
            "principal_type": "User",
            "action": "Action::\"submit\"",
            "resource_type": "Document",
            "reference_path": os.path.join(REFS, "submit_safety.cedar"),
        },
        {
            "name": "approve_safety",
            "description": "approve permitted only when predecessorAuthorized is present AND actionType == 'submit' AND actor != principal (SoD)",
            "type": "implies",
            "principal_type": "User",
            "action": "Action::\"approve\"",
            "resource_type": "Document",
            "reference_path": os.path.join(REFS, "approve_safety.cedar"),
        },

        # ── Floors ───────────────────────────────────────────────────────
        {
            "name": "floor_anyone_can_prepare",
            "description": "Any user MUST be permitted to prepare any document",
            "type": "floor",
            "principal_type": "User",
            "action": "Action::\"prepare\"",
            "resource_type": "Document",
            "floor_path": os.path.join(REFS, "floor_anyone_can_prepare.cedar"),
        },
        {
            "name": "floor_submit_after_prepare",
            "description": "submit MUST be permitted when the predecessor attestation says actionType == 'prepare'",
            "type": "floor",
            "principal_type": "User",
            "action": "Action::\"submit\"",
            "resource_type": "Document",
            "floor_path": os.path.join(REFS, "floor_submit_after_prepare.cedar"),
        },
        {
            "name": "floor_approve_after_submit_by_other",
            "description": "approve MUST be permitted when the predecessor attestation says actionType == 'submit' AND the submitter != principal",
            "type": "floor",
            "principal_type": "User",
            "action": "Action::\"approve\"",
            "resource_type": "Document",
            "floor_path": os.path.join(REFS, "floor_approve_after_submit_by_other.cedar"),
        },

        # ── Liveness ─────────────────────────────────────────────────────
        {
            "name": "liveness_prepare",
            "description": "User+prepare+Document liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": "Action::\"prepare\"",
            "resource_type": "Document",
        },
        {
            "name": "liveness_submit",
            "description": "User+submit+Document liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": "Action::\"submit\"",
            "resource_type": "Document",
        },
        {
            "name": "liveness_approve",
            "description": "User+approve+Document liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": "Action::\"approve\"",
            "resource_type": "Document",
        },
    ]
