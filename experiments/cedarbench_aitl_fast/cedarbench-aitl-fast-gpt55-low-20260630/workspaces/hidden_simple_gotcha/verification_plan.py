"""Verification plan for realworld/hidden_simple_gotcha.

File ownership transfer with a SUBTLE invariant: the schema carries
two distinct user-valued fields (`creator` immutable, `currentOwner`
mutable). The implicit business rule -- never spelled out as a single
sentence in the spec -- is that the creator retains read access
permanently, even after ownership transfers away. Transfer rights, in
contrast, belong to the current owner only; the creator cannot
reclaim.

The adversarial spec phrasing ("users can read files they own") tempts
the synthesizer to use only `principal == resource.currentOwner`, which
silently drops the creator-retention backdoor. Floor
`floor_creator_read_after_transfer` is the smoking-gun catcher: it
asserts the post-transfer case explicitly, where creator != currentOwner.

Symmetrically, a synthesizer that "fixes" by also adding creator to
`transfer` violates `transfer_safety`.

2 ceilings + 4 floors + 2 liveness.
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # -- Safety ceilings ------------------------------------------------
        {
            "name": "read_safety",
            "description": "read only when principal is currentOwner OR creator",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"read"',
            "resource_type": "File",
            "reference_path": os.path.join(REFS, "read_safety.cedar"),
        },
        {
            "name": "transfer_safety",
            "description": "transfer only when principal is currentOwner (creator may NOT)",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"transfer"',
            "resource_type": "File",
            "reference_path": os.path.join(REFS, "transfer_safety.cedar"),
        },

        # -- Floors ----------------------------------------------------------
        {
            "name": "floor_owner_read",
            "description": "current owner MUST be able to read",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"read"',
            "resource_type": "File",
            "floor_path": os.path.join(REFS, "floor_owner_read.cedar"),
        },
        {
            "name": "floor_creator_read",
            "description": "creator MUST be able to read (the hidden invariant)",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"read"',
            "resource_type": "File",
            "floor_path": os.path.join(REFS, "floor_creator_read.cedar"),
        },
        {
            "name": "floor_creator_read_after_transfer",
            "description": "creator MUST be able to read even when no longer current owner",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"read"',
            "resource_type": "File",
            "floor_path": os.path.join(REFS, "floor_creator_read_after_transfer.cedar"),
        },
        {
            "name": "floor_owner_transfer",
            "description": "current owner MUST be able to transfer",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"transfer"',
            "resource_type": "File",
            "floor_path": os.path.join(REFS, "floor_owner_transfer.cedar"),
        },

        # -- Liveness --------------------------------------------------------
        {
            "name": "liveness_read",
            "description": "at least one read must be permitted",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"read"',
            "resource_type": "File",
        },
        {
            "name": "liveness_transfer",
            "description": "at least one transfer must be permitted",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"transfer"',
            "resource_type": "File",
        },
    ]
