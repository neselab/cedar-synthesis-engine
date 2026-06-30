"""Hand-authored verification plan for realworld/compound_attestation_multi_signer.

Multi-signer governance gate. Tests:
  - Three optional record-typed context attributes, each with its own
    fields (signer, signedAt, validUntil).
  - Nine-clause conjunction with no single point of failure: each
    has-guard, set-membership check, distinctness inequality, and
    validity comparison contributes one clause.
  - Negated-has trap (§8.3): every read of context.attestationN.field
    must be preceded by a context-has guard for that record.

Hunts for the failure modes where the model:
  (a) drops one of the three has-guards (schema-validation failure),
  (b) omits a pairwise-distinctness clause (allowing one signer to
      attest twice), (c) checks signedAt instead of validUntil, (d)
      uses < instead of <= on validity.
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # -- Safety ceilings --------------------------------------------------
        {
            "name": "execute_safety",
            "description": (
                "execute permitted only when all 3 attestations present, "
                "each signer in requiredSigners, signers pairwise distinct, "
                "and each attestation valid (now <= validUntil)"
            ),
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"execute"',
            "resource_type": "Proposal",
            "reference_path": os.path.join(REFS, "execute_safety.cedar"),
        },
        {
            "name": "view_safety",
            "description": "view ceiling — view is open to any user",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"view"',
            "resource_type": "Proposal",
            "reference_path": os.path.join(REFS, "view_safety.cedar"),
        },

        # -- Floors -----------------------------------------------------------
        {
            "name": "execute_must_permit",
            "description": (
                "execute MUST be permitted when all 3 attestations are "
                "present, each signer in requiredSigners, distinct, and "
                "all currently valid"
            ),
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"execute"',
            "resource_type": "Proposal",
            "floor_path": os.path.join(REFS, "execute_must_permit.cedar"),
        },
        {
            "name": "view_must_permit",
            "description": "any user MUST be able to view any proposal",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"view"',
            "resource_type": "Proposal",
            "floor_path": os.path.join(REFS, "view_must_permit.cedar"),
        },

        # -- Liveness ---------------------------------------------------------
        {
            "name": "liveness_execute",
            "description": "User+execute+Proposal liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"execute"',
            "resource_type": "Proposal",
        },
        {
            "name": "liveness_view",
            "description": "User+view+Proposal liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"view"',
            "resource_type": "Proposal",
        },
    ]
