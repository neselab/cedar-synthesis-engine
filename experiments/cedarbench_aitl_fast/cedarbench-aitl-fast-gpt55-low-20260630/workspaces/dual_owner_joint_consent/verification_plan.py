"""Hand-authored verification plan for realworld/dual_owner_joint_consent.

Joint-consent pattern: a JointAsset has exactly two owners. Either may
view at any time, but `transfer` requires fresh signed consent from BOTH
owners — the two consent records may arrive in either order.

Hunts the failure mode where the model:
  - Forgets the order-symmetry on consents (only accepts
    consent1=owner1 / consent2=owner2 and rejects the swap), failing
    a hand-crafted floor that uses the swapped order — OR more likely
    fails the ceiling by accepting bogus signers.
  - Skips the freshness check on one of the two consents.
  - Forgets to require BOTH consents (single-consent transfer).
  - Drops a required `context has consentN` guard on the optional
    record fields (§8.3).
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # -- Safety ceilings --------------------------------------------------
        {
            "name": "view_safety",
            "description": (
                "view permitted only when principal is one of the two "
                "co-owners (owner1 or owner2)"
            ),
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"view"',
            "resource_type": "JointAsset",
            "reference_path": os.path.join(REFS, "view_safety.cedar"),
        },
        {
            "name": "transfer_safety",
            "description": (
                "transfer permitted only when BOTH consents present, "
                "signers match {owner1, owner2} in either order, and "
                "both signed within the last 24h"
            ),
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"transfer"',
            "resource_type": "JointAsset",
            "reference_path": os.path.join(REFS, "transfer_safety.cedar"),
        },

        # -- Floors -----------------------------------------------------------
        {
            "name": "owner1_must_view",
            "description": "owner1 MUST be permitted to view the asset",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"view"',
            "resource_type": "JointAsset",
            "floor_path": os.path.join(REFS, "owner1_must_view.cedar"),
        },
        {
            "name": "owner2_must_view",
            "description": "owner2 MUST be permitted to view the asset",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"view"',
            "resource_type": "JointAsset",
            "floor_path": os.path.join(REFS, "owner2_must_view.cedar"),
        },
        {
            "name": "transfer_with_fresh_consents_must_permit",
            "description": (
                "When both consents are present, signed by owner1 and "
                "owner2 (canonical order), and both fresh, transfer "
                "MUST be permitted"
            ),
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"transfer"',
            "resource_type": "JointAsset",
            "floor_path": os.path.join(
                REFS, "transfer_with_fresh_consents_must_permit.cedar"
            ),
        },

        # -- Liveness ---------------------------------------------------------
        {
            "name": "liveness_view",
            "description": "User+view+JointAsset liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"view"',
            "resource_type": "JointAsset",
        },
        {
            "name": "liveness_transfer",
            "description": "User+transfer+JointAsset liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"transfer"',
            "resource_type": "JointAsset",
        },
    ]
