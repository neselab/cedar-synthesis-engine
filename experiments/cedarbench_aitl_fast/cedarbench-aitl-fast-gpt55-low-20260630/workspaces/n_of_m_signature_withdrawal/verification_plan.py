"""Hand-authored verification plan for realworld/n_of_m_signature_withdrawal.

3-of-5 multi-signature governance with withdrawable signatures. Tests:
  - Threshold encoded WITHOUT .size() (Cedar has no such operator) by
    enumerating C(5,3) = 10 quorum subsets and checking each via
    .containsAll(...) on a dynamic context.activeSigners set.
  - Eligible-signer gating across four actions (executeProposal,
    viewProposal, addSignature, withdrawSignature).

Failure modes the harness will hunt:
  1. Using .contains on a single signer instead of .containsAll on a
     3-element subset (under-permits — execute_quorum floors fail).
  2. Using .containsAny across the full eligible set (over-permits — a
     single active signer would satisfy execute_safety, fails ceiling).
  3. Omitting some of the 10 subsets (under-permits specific quorums
     — e.g. dropping the {s3,s4,s5} disjunct fails execute_quorum_345).
  4. Omitting the eligible-signer principal restriction (over-permits
     non-eligible signers — fails ceilings on every action).
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # -- Safety ceilings (one per action) --------------------------------
        {
            "name": "execute_safety",
            "description": (
                "executeProposal permitted only when principal is one of "
                "the 5 eligible signers AND context.activeSigners contains "
                "at least one 3-of-5 subset (10 disjuncts via containsAll)"
            ),
            "type": "implies",
            "principal_type": "Signer",
            "action": 'Action::"executeProposal"',
            "resource_type": "Proposal",
            "reference_path": os.path.join(REFS, "execute_safety.cedar"),
        },
        {
            "name": "view_safety",
            "description": (
                "viewProposal permitted only for the 5 eligible signers"
            ),
            "type": "implies",
            "principal_type": "Signer",
            "action": 'Action::"viewProposal"',
            "resource_type": "Proposal",
            "reference_path": os.path.join(REFS, "view_safety.cedar"),
        },
        {
            "name": "add_safety",
            "description": (
                "addSignature permitted only for the 5 eligible signers"
            ),
            "type": "implies",
            "principal_type": "Signer",
            "action": 'Action::"addSignature"',
            "resource_type": "Proposal",
            "reference_path": os.path.join(REFS, "add_safety.cedar"),
        },
        {
            "name": "withdraw_safety",
            "description": (
                "withdrawSignature permitted only for the 5 eligible signers"
            ),
            "type": "implies",
            "principal_type": "Signer",
            "action": 'Action::"withdrawSignature"',
            "resource_type": "Proposal",
            "reference_path": os.path.join(REFS, "withdraw_safety.cedar"),
        },

        # -- Floors -----------------------------------------------------------
        {
            "name": "execute_quorum_123_must_permit",
            "description": (
                "When activeSigners contains {s1,s2,s3}, an eligible "
                "signer MUST be permitted to executeProposal"
            ),
            "type": "floor",
            "principal_type": "Signer",
            "action": 'Action::"executeProposal"',
            "resource_type": "Proposal",
            "floor_path": os.path.join(
                REFS, "execute_quorum_123_must_permit.cedar"
            ),
        },
        {
            "name": "execute_quorum_345_must_permit",
            "description": (
                "When activeSigners contains {s3,s4,s5} (the 'last' "
                "subset, common omission target), an eligible signer "
                "MUST be permitted to executeProposal"
            ),
            "type": "floor",
            "principal_type": "Signer",
            "action": 'Action::"executeProposal"',
            "resource_type": "Proposal",
            "floor_path": os.path.join(
                REFS, "execute_quorum_345_must_permit.cedar"
            ),
        },
        {
            "name": "view_must_permit",
            "description": (
                "Any of the 5 eligible signers MUST be permitted to view"
            ),
            "type": "floor",
            "principal_type": "Signer",
            "action": 'Action::"viewProposal"',
            "resource_type": "Proposal",
            "floor_path": os.path.join(REFS, "view_must_permit.cedar"),
        },
        {
            "name": "add_must_permit",
            "description": (
                "Any of the 5 eligible signers MUST be permitted to "
                "addSignature"
            ),
            "type": "floor",
            "principal_type": "Signer",
            "action": 'Action::"addSignature"',
            "resource_type": "Proposal",
            "floor_path": os.path.join(REFS, "add_must_permit.cedar"),
        },
        {
            "name": "withdraw_must_permit",
            "description": (
                "Any of the 5 eligible signers MUST be permitted to "
                "withdrawSignature"
            ),
            "type": "floor",
            "principal_type": "Signer",
            "action": 'Action::"withdrawSignature"',
            "resource_type": "Proposal",
            "floor_path": os.path.join(REFS, "withdraw_must_permit.cedar"),
        },

        # -- Liveness ---------------------------------------------------------
        {
            "name": "liveness_execute",
            "description": "Signer+executeProposal+Proposal liveness",
            "type": "always-denies-liveness",
            "principal_type": "Signer",
            "action": 'Action::"executeProposal"',
            "resource_type": "Proposal",
        },
        {
            "name": "liveness_view",
            "description": "Signer+viewProposal+Proposal liveness",
            "type": "always-denies-liveness",
            "principal_type": "Signer",
            "action": 'Action::"viewProposal"',
            "resource_type": "Proposal",
        },
        {
            "name": "liveness_add",
            "description": "Signer+addSignature+Proposal liveness",
            "type": "always-denies-liveness",
            "principal_type": "Signer",
            "action": 'Action::"addSignature"',
            "resource_type": "Proposal",
        },
        {
            "name": "liveness_withdraw",
            "description": "Signer+withdrawSignature+Proposal liveness",
            "type": "always-denies-liveness",
            "principal_type": "Signer",
            "action": 'Action::"withdrawSignature"',
            "resource_type": "Proposal",
        },
    ]
