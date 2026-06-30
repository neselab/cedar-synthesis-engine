"""Hand-authored verification plan for realworld/fifteen_optional_context.

Federated identity gateway with fifteen optional context booleans, of
which a fixed conjunction of FIVE specific attestations is required:
mfaToken AND deviceTrusted AND locationVerified AND identityProofed
AND auditLoggingEnabled.

Stresses §8.3 (negated-`has` / has-guard discipline) by requiring
five paired has-guard + read clauses in a single conjunction. The
ten unused optional attributes are present in the schema as
forward-compatibility carriers and must not appear in the policy.

Plan:
  - 1 ceiling: access permitted ONLY when the five required
    attestations are all present and true.
  - 2 floors:
      - all_five_must_permit: when the five required attestations
        are present+true, access MUST be permitted.
      - extra_attestations_must_permit: pins the policy to NOT
        accidentally require any of the other ten optional
        attributes (here `complianceFlag` is present and false).
  - 1 liveness check.
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # ── Safety ceiling ──────────────────────────────────────────────
        {
            "name": "access_safety",
            "description": "accessFederatedResource permitted only when all five required attestations are present and true",
            "type": "implies",
            "principal_type": "User",
            "action": "Action::\"accessFederatedResource\"",
            "resource_type": "Resource",
            "reference_path": os.path.join(REFS, "access_safety.cedar"),
        },

        # ── Floors ──────────────────────────────────────────────────────
        {
            "name": "all_five_must_permit",
            "description": "When the five required attestations are present and true, access MUST be permitted",
            "type": "floor",
            "principal_type": "User",
            "action": "Action::\"accessFederatedResource\"",
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, "all_five_must_permit.cedar"),
        },
        {
            "name": "extra_attestations_must_permit",
            "description": "Policy must NOT require any of the other ten optional attestations (e.g. complianceFlag may be present and false)",
            "type": "floor",
            "principal_type": "User",
            "action": "Action::\"accessFederatedResource\"",
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, "extra_attestations_must_permit.cedar"),
        },

        # ── Liveness ────────────────────────────────────────────────────
        {
            "name": "liveness_access",
            "description": "User+accessFederatedResource+Resource liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": "Action::\"accessFederatedResource\"",
            "resource_type": "Resource",
        },
    ]
