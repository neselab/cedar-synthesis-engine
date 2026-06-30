"""Hand-authored verification plan for realworld/priority_ordered_requirements.

Three rules apply to record access with explicit priority:
  R1 (HIGHEST): legalHold       => legal_team only.
  R2 (MEDIUM):  containsPII     => pii_clearance only (when not on hold).
  R3 (LOWEST):  default          => role == "reader" (when neither
                                    legalHold nor containsPII applies).

The encoding pattern under test is: lower-priority rules MUST carry
explicit negations of every higher-priority rule's trigger condition
in their `when` guard. A naive disjunction
(R1_perm || R2_perm || R3_perm) is too permissive and fails the
ceiling because a `reader` would access PII records (R3 firing while
R2's gate is true) and a cleared user would access legal-hold records
(R2 firing while R1's gate is true).

Floors prove the precedence chain in both directions:
  - Each rule independently must permit its own canonical case.
  - When R1 and R2 both apply, legal_team accesses regardless of
    pii_clearance — confirming R1 strictly dominates R2.

Hunts for failure modes where the model writes a disjunction without
priority guards, or drops the role/clearance checks under the (false)
assumption that priority alone is sufficient.
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # -- Safety ceiling ---------------------------------------------------
        {
            "name": "access_safety",
            "description": (
                "access permitted only under the priority chain: "
                "R1 legal_team for legal-hold records; R2 cleared "
                "users for PII (no hold); R3 readers for plain records."
            ),
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"access"',
            "resource_type": "Record",
            "reference_path": os.path.join(REFS, "access_safety.cedar"),
        },

        # -- Floors -----------------------------------------------------------
        {
            "name": "floor_legal_team_on_hold",
            "description": (
                "R1 must fire: legal_team MUST access a legal-hold "
                "record (containsPII pinned false)."
            ),
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"access"',
            "resource_type": "Record",
            "floor_path": os.path.join(REFS, "floor_legal_team_on_hold.cedar"),
        },
        {
            "name": "floor_cleared_pii_access",
            "description": (
                "R2 must fire: a user with pii_clearance MUST access "
                "a non-legal-hold PII record."
            ),
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"access"',
            "resource_type": "Record",
            "floor_path": os.path.join(
                REFS, "floor_cleared_pii_access.cedar"
            ),
        },
        {
            "name": "floor_reader_default_access",
            "description": (
                "R3 must fire: a reader MUST access a plain record "
                "(no legal hold, no PII)."
            ),
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"access"',
            "resource_type": "Record",
            "floor_path": os.path.join(
                REFS, "floor_reader_default_access.cedar"
            ),
        },
        {
            "name": "floor_legal_team_on_hold_with_pii",
            "description": (
                "Precedence: when R1 and R2 both apply, R1 wins. "
                "legal_team without pii_clearance MUST access a "
                "record under both legal hold and containsPII."
            ),
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"access"',
            "resource_type": "Record",
            "floor_path": os.path.join(
                REFS, "floor_legal_team_on_hold_with_pii.cedar"
            ),
        },

        # -- Liveness ---------------------------------------------------------
        {
            "name": "liveness_access",
            "description": "User+access+Record liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"access"',
            "resource_type": "Record",
        },
    ]
