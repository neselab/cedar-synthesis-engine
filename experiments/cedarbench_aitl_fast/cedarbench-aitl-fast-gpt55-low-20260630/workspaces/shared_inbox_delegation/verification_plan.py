"""Verification plan for realworld/shared_inbox_delegation.

Enterprise shared-mailbox scenario with three-tier role hierarchy:
owner > delegate > member. Tests Set.contains() membership checks
and per-action role gating across readMail, sendAs, manageFolders,
grantAccess.

Key verification goals:
  - Members can read but NOT sendAs (the delegate/member split)
  - Delegates can read and sendAs but NOT manageFolders or grantAccess
  - Owner has full control across all four actions
  - Liveness holds for every action (symcc-compatible via Set.contains)
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # -- Safety ceilings ------------------------------------------------
        {
            "name": "readMail_safety",
            "description": "readMail only when owner OR delegate OR member",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"readMail"',
            "resource_type": "Mailbox",
            "reference_path": os.path.join(REFS, "readMail_safety.cedar"),
        },
        {
            "name": "sendAs_safety",
            "description": "sendAs only when owner OR delegate (not members)",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"sendAs"',
            "resource_type": "Mailbox",
            "reference_path": os.path.join(REFS, "sendAs_safety.cedar"),
        },
        {
            "name": "manageFolders_safety",
            "description": "manageFolders only when owner",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"manageFolders"',
            "resource_type": "Mailbox",
            "reference_path": os.path.join(REFS, "manageFolders_safety.cedar"),
        },
        {
            "name": "grantAccess_safety",
            "description": "grantAccess only when owner",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"grantAccess"',
            "resource_type": "Mailbox",
            "reference_path": os.path.join(REFS, "grantAccess_safety.cedar"),
        },

        # -- Floors ----------------------------------------------------------
        {
            "name": "floor_owner_readMail",
            "description": "owner MUST be able to readMail",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"readMail"',
            "resource_type": "Mailbox",
            "floor_path": os.path.join(REFS, "floor_owner_readMail.cedar"),
        },
        {
            "name": "floor_member_readMail",
            "description": "member MUST be able to readMail",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"readMail"',
            "resource_type": "Mailbox",
            "floor_path": os.path.join(REFS, "floor_member_readMail.cedar"),
        },
        {
            "name": "floor_delegate_sendAs",
            "description": "delegate MUST be able to sendAs",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"sendAs"',
            "resource_type": "Mailbox",
            "floor_path": os.path.join(REFS, "floor_delegate_sendAs.cedar"),
        },
        {
            "name": "floor_owner_manageFolders",
            "description": "owner MUST be able to manageFolders",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"manageFolders"',
            "resource_type": "Mailbox",
            "floor_path": os.path.join(REFS, "floor_owner_manageFolders.cedar"),
        },

        # -- Liveness --------------------------------------------------------
        {
            "name": "liveness_readMail",
            "description": "at least one readMail must be permitted",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"readMail"',
            "resource_type": "Mailbox",
        },
        {
            "name": "liveness_sendAs",
            "description": "at least one sendAs must be permitted",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"sendAs"',
            "resource_type": "Mailbox",
        },
        {
            "name": "liveness_manageFolders",
            "description": "at least one manageFolders must be permitted",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"manageFolders"',
            "resource_type": "Mailbox",
        },
        {
            "name": "liveness_grantAccess",
            "description": "at least one grantAccess must be permitted",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"grantAccess"',
            "resource_type": "Mailbox",
        },
    ]
