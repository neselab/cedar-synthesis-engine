"""Verification plan for realworld/reserved_keyword_attr_name.

Tests Cedar's reserved-keyword constraints on attribute names. The schema
uses attribute names that flirt with Cedar reserved-word space
(`inGroup`, `hasAccess`, `likedItems`, `permits`) -- a careless synthesizer
might slip into bare `in`, `has`, `like`, `permit`, all of which are
reserved identifiers that the parser rejects.
"""
import os
REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")

def get_checks():
    return [
        # Ceilings (implies): candidate must be NO MORE permissive than reference.
        {"name": "read_safety", "description": "read only when member or public+hasAccess", "type": "implies", "principal_type": "Member", "action": 'Action::"read"', "resource_type": "Channel", "reference_path": os.path.join(REFS, "read_safety.cedar")},
        {"name": "post_safety", "description": "post only when member with post capability", "type": "implies", "principal_type": "Member", "action": 'Action::"post"', "resource_type": "Channel", "reference_path": os.path.join(REFS, "post_safety.cedar")},
        {"name": "pin_safety", "description": "pin only when member with pin capability and pinning affinity", "type": "implies", "principal_type": "Member", "action": 'Action::"pin"', "resource_type": "Channel", "reference_path": os.path.join(REFS, "pin_safety.cedar")},

        # Floors: candidate must be AT LEAST as permissive as reference.
        {"name": "floor_member_read", "description": "members MUST be permitted to read their channels", "type": "floor", "principal_type": "Member", "action": 'Action::"read"', "resource_type": "Channel", "floor_path": os.path.join(REFS, "floor_member_read.cedar")},
        {"name": "floor_public_read", "description": "hasAccess members MUST read public channels", "type": "floor", "principal_type": "Member", "action": 'Action::"read"', "resource_type": "Channel", "floor_path": os.path.join(REFS, "floor_public_read.cedar")},
        {"name": "floor_member_post", "description": "members with post capability MUST be permitted to post", "type": "floor", "principal_type": "Member", "action": 'Action::"post"', "resource_type": "Channel", "floor_path": os.path.join(REFS, "floor_member_post.cedar")},
        {"name": "floor_member_pin", "description": "members with pin capability and pinning affinity MUST be permitted to pin", "type": "floor", "principal_type": "Member", "action": 'Action::"pin"', "resource_type": "Channel", "floor_path": os.path.join(REFS, "floor_member_pin.cedar")},

        # Liveness: at least one request must be permitted.
        {"name": "liveness_read", "description": "at least one read permitted", "type": "always-denies-liveness", "principal_type": "Member", "action": 'Action::"read"', "resource_type": "Channel"},
        {"name": "liveness_post", "description": "at least one post permitted", "type": "always-denies-liveness", "principal_type": "Member", "action": 'Action::"post"', "resource_type": "Channel"},
        {"name": "liveness_pin", "description": "at least one pin permitted", "type": "always-denies-liveness", "principal_type": "Member", "action": 'Action::"pin"', "resource_type": "Channel"},
    ]
