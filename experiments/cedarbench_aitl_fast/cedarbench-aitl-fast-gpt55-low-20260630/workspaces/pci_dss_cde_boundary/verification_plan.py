"""Hand-authored verification plan for realworld/pci_dss_cde_boundary.

PCI DSS scope reduction via tokenization. Tests:
  - Non-User principal type (System)
  - Data-classification gating (PAN vs TOKEN vs MASKED_PAN)
  - Cardholder data environment (CDE) boundary — both principal
    (cdeAuthorized) and resource (cdeMember) checks for PAN reads
  - Dual-attribute requirement on detokenize (cdeAuthorized AND
    auditCompliant)
  - Data-type-conditional audit gate — auditing PAN requires
    cdeAuthorized; non-PAN audits do not
  - §8.8 floor-bound consistency: every PAN-touching floor includes
    the CDE check so it is jointly satisfiable with the ceiling.
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # ── Safety ceilings (one per action) ─────────────────────────────
        {
            "name": "read_safety",
            "description": (
                "read permitted only when (PAN AND principal.cdeAuthorized "
                "AND resource.cdeMember) OR TOKEN OR MASKED_PAN"
            ),
            "type": "implies",
            "principal_type": "System",
            "action": "Action::\"read\"",
            "resource_type": "PaymentRecord",
            "reference_path": os.path.join(REFS, "read_safety.cedar"),
        },
        {
            "name": "tokenize_safety",
            "description": (
                "tokenize permitted only when principal.cdeAuthorized AND "
                "resource.dataType == \"PAN\""
            ),
            "type": "implies",
            "principal_type": "System",
            "action": "Action::\"tokenize\"",
            "resource_type": "PaymentRecord",
            "reference_path": os.path.join(REFS, "tokenize_safety.cedar"),
        },
        {
            "name": "detokenize_safety",
            "description": (
                "detokenize permitted only when principal.cdeAuthorized "
                "AND principal.auditCompliant AND resource.dataType == \"TOKEN\""
            ),
            "type": "implies",
            "principal_type": "System",
            "action": "Action::\"detokenize\"",
            "resource_type": "PaymentRecord",
            "reference_path": os.path.join(REFS, "detokenize_safety.cedar"),
        },
        {
            "name": "audit_safety",
            "description": (
                "audit permitted only when resource.dataType != \"PAN\" OR "
                "principal.cdeAuthorized"
            ),
            "type": "implies",
            "principal_type": "System",
            "action": "Action::\"audit\"",
            "resource_type": "PaymentRecord",
            "reference_path": os.path.join(REFS, "audit_safety.cedar"),
        },

        # ── Floors ───────────────────────────────────────────────────────
        {
            "name": "floor_read_pan",
            "description": (
                "CDE-authorized System reading a PAN that is itself a CDE "
                "member MUST be permitted"
            ),
            "type": "floor",
            "principal_type": "System",
            "action": "Action::\"read\"",
            "resource_type": "PaymentRecord",
            "floor_path": os.path.join(REFS, "floor_read_pan.cedar"),
        },
        {
            "name": "floor_read_token",
            "description": "Any System reading a TOKEN MUST be permitted",
            "type": "floor",
            "principal_type": "System",
            "action": "Action::\"read\"",
            "resource_type": "PaymentRecord",
            "floor_path": os.path.join(REFS, "floor_read_token.cedar"),
        },
        {
            "name": "floor_read_masked",
            "description": "Any System reading a MASKED_PAN MUST be permitted",
            "type": "floor",
            "principal_type": "System",
            "action": "Action::\"read\"",
            "resource_type": "PaymentRecord",
            "floor_path": os.path.join(REFS, "floor_read_masked.cedar"),
        },
        {
            "name": "floor_tokenize_pan",
            "description": (
                "CDE-authorized System tokenizing a PAN MUST be permitted"
            ),
            "type": "floor",
            "principal_type": "System",
            "action": "Action::\"tokenize\"",
            "resource_type": "PaymentRecord",
            "floor_path": os.path.join(REFS, "floor_tokenize_pan.cedar"),
        },
        {
            "name": "floor_detokenize",
            "description": (
                "System with BOTH cdeAuthorized and auditCompliant "
                "detokenizing a TOKEN MUST be permitted"
            ),
            "type": "floor",
            "principal_type": "System",
            "action": "Action::\"detokenize\"",
            "resource_type": "PaymentRecord",
            "floor_path": os.path.join(REFS, "floor_detokenize.cedar"),
        },
        {
            "name": "floor_audit_token",
            "description": "Any System auditing a TOKEN MUST be permitted",
            "type": "floor",
            "principal_type": "System",
            "action": "Action::\"audit\"",
            "resource_type": "PaymentRecord",
            "floor_path": os.path.join(REFS, "floor_audit_token.cedar"),
        },

        # ── Liveness ─────────────────────────────────────────────────────
        {
            "name": "liveness_read",
            "description": "System+read+PaymentRecord liveness",
            "type": "always-denies-liveness",
            "principal_type": "System",
            "action": "Action::\"read\"",
            "resource_type": "PaymentRecord",
        },
        {
            "name": "liveness_tokenize",
            "description": "System+tokenize+PaymentRecord liveness",
            "type": "always-denies-liveness",
            "principal_type": "System",
            "action": "Action::\"tokenize\"",
            "resource_type": "PaymentRecord",
        },
        {
            "name": "liveness_detokenize",
            "description": "System+detokenize+PaymentRecord liveness",
            "type": "always-denies-liveness",
            "principal_type": "System",
            "action": "Action::\"detokenize\"",
            "resource_type": "PaymentRecord",
        },
        {
            "name": "liveness_audit",
            "description": "System+audit+PaymentRecord liveness",
            "type": "always-denies-liveness",
            "principal_type": "System",
            "action": "Action::\"audit\"",
            "resource_type": "PaymentRecord",
        },
    ]
