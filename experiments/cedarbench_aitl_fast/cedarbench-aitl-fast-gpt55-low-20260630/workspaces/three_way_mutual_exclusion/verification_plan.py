"""Hand-authored verification plan for realworld/three_way_mutual_exclusion.

Three-way pairwise SoD across submit/approve/audit on a ChangeRequest.
The same Engineer must not perform any two of the three actions for a
given request. Prior-actor identity is supplied as optional context
attributes.

Failure modes the harness must catch:
- Forgetting one of the two pairwise checks for an action.
- Skipping a `has`-guard on an optional context attribute.
- Encoding the wrong cross-action mapping (e.g. excluding prevApprover
  on the audit action, which is only HALF of the audit-side SoD).
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # ── Safety ceilings ──────────────────────────────────────────────
        {"name": "submit_safety", "description": "submit permitted only when principal != prevApprover (if present) AND principal != prevAuditor (if present)", "type": "implies", "principal_type": "Engineer", "action": "Action::\"submit\"", "resource_type": "ChangeRequest", "reference_path": os.path.join(REFS, "submit_safety.cedar")},
        {"name": "approve_safety", "description": "approve permitted only when principal != prevSubmitter (if present) AND principal != prevAuditor (if present)", "type": "implies", "principal_type": "Engineer", "action": "Action::\"approve\"", "resource_type": "ChangeRequest", "reference_path": os.path.join(REFS, "approve_safety.cedar")},
        {"name": "audit_safety", "description": "audit permitted only when principal != prevSubmitter (if present) AND principal != prevApprover (if present)", "type": "implies", "principal_type": "Engineer", "action": "Action::\"audit\"", "resource_type": "ChangeRequest", "reference_path": os.path.join(REFS, "audit_safety.cedar")},

        # ── Floors ───────────────────────────────────────────────────────
        {"name": "fresh_submit_must_permit", "description": "Any Engineer MUST submit a fresh ChangeRequest (no prev attestations)", "type": "floor", "principal_type": "Engineer", "action": "Action::\"submit\"", "resource_type": "ChangeRequest", "floor_path": os.path.join(REFS, "fresh_submit_must_permit.cedar")},
        {"name": "fresh_approve_must_permit", "description": "Any Engineer MUST approve a ChangeRequest with no prev attestations", "type": "floor", "principal_type": "Engineer", "action": "Action::\"approve\"", "resource_type": "ChangeRequest", "floor_path": os.path.join(REFS, "fresh_approve_must_permit.cedar")},
        {"name": "fresh_audit_must_permit", "description": "Any Engineer MUST audit a ChangeRequest with no prev attestations", "type": "floor", "principal_type": "Engineer", "action": "Action::\"audit\"", "resource_type": "ChangeRequest", "floor_path": os.path.join(REFS, "fresh_audit_must_permit.cedar")},
        {"name": "audit_by_third_party_must_permit", "description": "An Engineer who is neither prevSubmitter nor prevApprover MUST be permitted to audit", "type": "floor", "principal_type": "Engineer", "action": "Action::\"audit\"", "resource_type": "ChangeRequest", "floor_path": os.path.join(REFS, "audit_by_third_party_must_permit.cedar")},

        # ── Liveness ─────────────────────────────────────────────────────
        {"name": "liveness_submit", "description": "Engineer+submit+ChangeRequest liveness", "type": "always-denies-liveness", "principal_type": "Engineer", "action": "Action::\"submit\"", "resource_type": "ChangeRequest"},
        {"name": "liveness_approve", "description": "Engineer+approve+ChangeRequest liveness", "type": "always-denies-liveness", "principal_type": "Engineer", "action": "Action::\"approve\"", "resource_type": "ChangeRequest"},
        {"name": "liveness_audit", "description": "Engineer+audit+ChangeRequest liveness", "type": "always-denies-liveness", "principal_type": "Engineer", "action": "Action::\"audit\"", "resource_type": "ChangeRequest"},
    ]
