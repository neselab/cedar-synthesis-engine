"""Hand-authored verification plan for realworld/pii_data_classification.

Classic Multi-Level Security (MLS) pattern with hierarchical data
classification, user clearance, PII training gate, and need-to-know
compartmentalization. Tests:
  - String-enum hierarchy encoded as explicit disjunctions (Cedar has
    no enum ordering)
  - Action variants with different clearance requirements (read vs
    download, with download one tier stricter)
  - Compositional forbids (PII, need-to-know) that stack on top of
    the base clearance check
  - Restricted data that can be read but never downloaded
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # ── Safety ceilings ──────────────────────────────────────────────
        {"name": "read_safety", "description": "readDocument permitted only when clearance dominates classification AND PII gate AND need-to-know (for Restricted)", "type": "implies", "principal_type": "User", "action": "Action::\"readDocument\"", "resource_type": "Document", "reference_path": os.path.join(REFS, "read_safety.cedar")},
        {"name": "download_safety", "description": "downloadDocument permitted only when clearance is one level higher than classification AND classification != Restricted AND PII gate", "type": "implies", "principal_type": "User", "action": "Action::\"downloadDocument\"", "resource_type": "Document", "reference_path": os.path.join(REFS, "download_safety.cedar")},

        # ── Floors ───────────────────────────────────────────────────────
        {"name": "l1_must_read_public_no_pii", "description": "L1 user MUST read a Public non-PII document", "type": "floor", "principal_type": "User", "action": "Action::\"readDocument\"", "resource_type": "Document", "floor_path": os.path.join(REFS, "l1_must_read_public_no_pii.cedar")},
        {"name": "l3_must_read_confidential_no_pii", "description": "L3 user MUST read a Confidential non-PII document", "type": "floor", "principal_type": "User", "action": "Action::\"readDocument\"", "resource_type": "Document", "floor_path": os.path.join(REFS, "l3_must_read_confidential_no_pii.cedar")},
        {"name": "l4_ntk_must_read_restricted", "description": "L4 user in needToKnow MUST read a Restricted non-PII document", "type": "floor", "principal_type": "User", "action": "Action::\"readDocument\"", "resource_type": "Document", "floor_path": os.path.join(REFS, "l4_ntk_must_read_restricted.cedar")},
        {"name": "l4_must_download_confidential_no_pii", "description": "L4 user MUST download a Confidential non-PII document", "type": "floor", "principal_type": "User", "action": "Action::\"downloadDocument\"", "resource_type": "Document", "floor_path": os.path.join(REFS, "l4_must_download_confidential_no_pii.cedar")},

        # ── Liveness ─────────────────────────────────────────────────────
        {"name": "liveness_read", "description": "User+readDocument+Document liveness", "type": "always-denies-liveness", "principal_type": "User", "action": "Action::\"readDocument\"", "resource_type": "Document"},
        {"name": "liveness_download", "description": "User+downloadDocument+Document liveness", "type": "always-denies-liveness", "principal_type": "User", "action": "Action::\"downloadDocument\"", "resource_type": "Document"},
    ]
