"""Hand-authored verification plan for realworld/conflicting_attestation_sources.

Two parallel attribute sources (resource.recordedOwner and an optional
context.claimedOwner) must agree when both speak. The scenario hunts
several common failure modes:

  - Candidate forgets the has-guard on context.claimedOwner, producing
    a policy that fails Cedar's type-checker (§8.3).
  - Candidate writes the optional check as
      `!(context has claimedOwner) || context.claimedOwner == X`
    and is rejected by the type-checker because negation does not
    propagate through `has` (§5.4 / §8.3 negated-`has` trap).
  - Candidate treats `view` and `transfer` symmetrically, allowing
    `transfer` to proceed on silence (claim absent). Per spec, transfer
    requires affirmative attestation.
  - Candidate forgets to enforce `principal == recordedOwner` in
    `transfer`, allowing a non-owner who happens to assert the correct
    owner to transfer the document.
  - Candidate accidentally allows `view` when claimedOwner is present
    but disagrees with recordedOwner (the core "conflicting sources"
    bug this scenario is built to detect).

7 checks total: 2 ceilings + 3 floors + 2 liveness.
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # -- Safety ceilings ------------------------------------------------
        {
            "name": "view_safety",
            "description": "view permitted only when principal == recordedOwner AND (claimedOwner absent OR claimedOwner == recordedOwner)",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"view"',
            "resource_type": "Document",
            "reference_path": os.path.join(REFS, "view_safety.cedar"),
        },
        {
            "name": "transfer_safety",
            "description": "transfer permitted only when claimedOwner is present AND claimedOwner == recordedOwner == principal (all three agree)",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"transfer"',
            "resource_type": "Document",
            "reference_path": os.path.join(REFS, "transfer_safety.cedar"),
        },

        # -- Floors (positive assertions) -----------------------------------
        {
            "name": "floor_view_silent",
            "description": "owner with no claimedOwner asserted MUST be permitted to view (legacy / silent caller)",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"view"',
            "resource_type": "Document",
            "floor_path": os.path.join(REFS, "floor_view_silent.cedar"),
        },
        {
            "name": "floor_view_agreeing",
            "description": "owner who asserts the correct claimedOwner MUST be permitted to view (attesting caller)",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"view"',
            "resource_type": "Document",
            "floor_path": os.path.join(REFS, "floor_view_agreeing.cedar"),
        },
        {
            "name": "floor_transfer_agreeing",
            "description": "owner with claimedOwner present and equal to recordedOwner MUST be permitted to transfer (all three agree)",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"transfer"',
            "resource_type": "Document",
            "floor_path": os.path.join(REFS, "floor_transfer_agreeing.cedar"),
        },

        # -- Liveness -------------------------------------------------------
        {
            "name": "liveness_view",
            "description": "User+view+Document liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"view"',
            "resource_type": "Document",
        },
        {
            "name": "liveness_transfer",
            "description": "User+transfer+Document liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"transfer"',
            "resource_type": "Document",
        },
    ]
