"""Hand-authored verification plan for realworld/red_herring_attributes.

Adversarial focus test: schema declares 18 attributes across User and
Document, but only 3 (User.role, User.mfaVerified, Document.owner) are
relevant to the rule. The synthesizer must ignore the noise.

Checks:
  - 1 ceiling: view_safety -- candidate cannot exceed (role in {reader,
    admin}) AND mfaVerified AND principal == owner.
  - 2 floors: reader-owner-mfa and admin-owner-mfa MUST be permitted.
    A candidate that gates on any red-herring attribute (accountTier,
    department, timezone, viewCount, etc.) will block these floors.
  - 1 liveness: at least one View+User+Document request is permitted.
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # -- Safety ceiling -------------------------------------------------
        {
            "name": "view_safety",
            "description": (
                "view permitted only when role in {reader, admin}, MFA "
                "verified, and principal == resource.owner"
            ),
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"view"',
            "resource_type": "Document",
            "reference_path": os.path.join(REFS, "view_safety.cedar"),
        },

        # -- Floors --------------------------------------------------------
        {
            "name": "floor_reader_owner_view",
            "description": (
                "reader with MFA who owns the document MUST be permitted "
                "to view"
            ),
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"view"',
            "resource_type": "Document",
            "floor_path": os.path.join(REFS, "floor_reader_owner_view.cedar"),
        },
        {
            "name": "floor_admin_owner_view",
            "description": (
                "admin with MFA who owns the document MUST be permitted "
                "to view"
            ),
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"view"',
            "resource_type": "Document",
            "floor_path": os.path.join(REFS, "floor_admin_owner_view.cedar"),
        },

        # -- Liveness ------------------------------------------------------
        {
            "name": "liveness_view",
            "description": "User+view+Document liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"view"',
            "resource_type": "Document",
        },
    ]
