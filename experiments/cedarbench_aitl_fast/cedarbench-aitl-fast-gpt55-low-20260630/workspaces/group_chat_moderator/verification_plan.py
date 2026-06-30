"""Verification plan for realworld/group_chat_moderator.
Discord/Slack-style channel moderation with owner/moderator/member tiers.
"""
import os
REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")

def get_checks():
    return [
        {"name": "read_safety", "description": "read only when member AND not archived", "type": "implies", "principal_type": "User", "action": 'Action::"read"', "resource_type": "Channel", "reference_path": os.path.join(REFS, "read_safety.cedar")},
        {"name": "post_safety", "description": "post only when member AND not archived", "type": "implies", "principal_type": "User", "action": 'Action::"post"', "resource_type": "Channel", "reference_path": os.path.join(REFS, "post_safety.cedar")},
        {"name": "delete_message_safety", "description": "deleteMessage only when owner or moderator", "type": "implies", "principal_type": "User", "action": 'Action::"deleteMessage"', "resource_type": "Channel", "reference_path": os.path.join(REFS, "delete_message_safety.cedar")},
        {"name": "pin_safety", "description": "pin only when owner or moderator", "type": "implies", "principal_type": "User", "action": 'Action::"pin"', "resource_type": "Channel", "reference_path": os.path.join(REFS, "pin_safety.cedar")},
        {"name": "archive_safety", "description": "archive only when owner", "type": "implies", "principal_type": "User", "action": 'Action::"archive"', "resource_type": "Channel", "reference_path": os.path.join(REFS, "archive_safety.cedar")},
        {"name": "floor_member_read", "description": "member MUST read non-archived", "type": "floor", "principal_type": "User", "action": 'Action::"read"', "resource_type": "Channel", "floor_path": os.path.join(REFS, "floor_member_read.cedar")},
        {"name": "floor_member_post", "description": "member MUST post non-archived", "type": "floor", "principal_type": "User", "action": 'Action::"post"', "resource_type": "Channel", "floor_path": os.path.join(REFS, "floor_member_post.cedar")},
        {"name": "floor_owner_delete", "description": "owner MUST deleteMessage", "type": "floor", "principal_type": "User", "action": 'Action::"deleteMessage"', "resource_type": "Channel", "floor_path": os.path.join(REFS, "floor_owner_delete.cedar")},
        {"name": "floor_moderator_pin", "description": "moderator MUST pin", "type": "floor", "principal_type": "User", "action": 'Action::"pin"', "resource_type": "Channel", "floor_path": os.path.join(REFS, "floor_moderator_pin.cedar")},
        {"name": "floor_owner_archive", "description": "owner MUST archive", "type": "floor", "principal_type": "User", "action": 'Action::"archive"', "resource_type": "Channel", "floor_path": os.path.join(REFS, "floor_owner_archive.cedar")},
        {"name": "liveness_read", "description": "at least one read permitted", "type": "always-denies-liveness", "principal_type": "User", "action": 'Action::"read"', "resource_type": "Channel"},
        {"name": "liveness_post", "description": "at least one post permitted", "type": "always-denies-liveness", "principal_type": "User", "action": 'Action::"post"', "resource_type": "Channel"},
        {"name": "liveness_deleteMessage", "description": "at least one deleteMessage permitted", "type": "always-denies-liveness", "principal_type": "User", "action": 'Action::"deleteMessage"', "resource_type": "Channel"},
        {"name": "liveness_archive", "description": "at least one archive permitted", "type": "always-denies-liveness", "principal_type": "User", "action": 'Action::"archive"', "resource_type": "Channel"},
    ]
