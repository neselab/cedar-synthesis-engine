"""Hand-authored verification plan for realworld/aml_kyc_tiered.

AML risk-based tiered Customer Due Diligence (CDD) for a retail bank.
Tests:
  - Three KYC tiers (SDD / CDD / EDD) gating four actions with
    distinct verification depths.
  - Amount-band conditioning on transferOut (three bands).
  - Risk-score branching on openProduct (high-risk EDD path vs.
    standard CDD/EDD path).
  - Multi-attribute attestation conjunction (uboVerified AND
    adverseMediaClean) on the high-amount and high-risk paths.

Hunts for failure modes where the model:
  (a) encodes "SDD blocked from large transfers" as a forbid on
      kycTier=="SDD" instead of as positive permits per band (§8.6),
  (b) forgets uboVerified + adverseMediaClean on the high-amount
      transferOut or the high-risk openProduct,
  (c) permits SDD to open products or escalate reviews,
  (d) permits SDD to perform mid- or large-band transfers.
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # -- Safety ceilings (one per action) --------------------------------
        {
            "name": "view_account_safety",
            "description": (
                "viewAccount permitted only for an onboarded BankCustomer "
                "(kycTier in SDD / CDD / EDD)"
            ),
            "type": "implies",
            "principal_type": "BankCustomer",
            "action": 'Action::"viewAccount"',
            "resource_type": "BankCustomer",
            "reference_path": os.path.join(REFS, "view_account_safety.cedar"),
        },
        {
            "name": "transfer_out_safety",
            "description": (
                "transferOut permitted only when verification depth matches "
                "the amount band (small: any tier, mid: CDD/EDD, large: "
                "EDD + uboVerified + adverseMediaClean)"
            ),
            "type": "implies",
            "principal_type": "BankCustomer",
            "action": 'Action::"transferOut"',
            "resource_type": "Transaction",
            "reference_path": os.path.join(REFS, "transfer_out_safety.cedar"),
        },
        {
            "name": "open_product_safety",
            "description": (
                "openProduct permitted only for high-risk EDD with full "
                "attestations OR standard-risk CDD/EDD"
            ),
            "type": "implies",
            "principal_type": "BankCustomer",
            "action": 'Action::"openProduct"',
            "resource_type": "BankCustomer",
            "reference_path": os.path.join(REFS, "open_product_safety.cedar"),
        },
        {
            "name": "escalate_review_safety",
            "description": (
                "escalateReview permitted only for compliance-aware tiers "
                "(CDD or EDD)"
            ),
            "type": "implies",
            "principal_type": "BankCustomer",
            "action": 'Action::"escalateReview"',
            "resource_type": "BankCustomer",
            "reference_path": os.path.join(
                REFS, "escalate_review_safety.cedar"
            ),
        },

        # -- Floors -----------------------------------------------------------
        {
            "name": "floor_view_account_sdd",
            "description": (
                "An SDD customer MUST be able to view their own account"
            ),
            "type": "floor",
            "principal_type": "BankCustomer",
            "action": 'Action::"viewAccount"',
            "resource_type": "BankCustomer",
            "floor_path": os.path.join(REFS, "floor_view_account_sdd.cedar"),
        },
        {
            "name": "floor_transfer_small_sdd",
            "description": (
                "An SDD customer MUST be permitted a small transfer "
                "(amount < 10000)"
            ),
            "type": "floor",
            "principal_type": "BankCustomer",
            "action": 'Action::"transferOut"',
            "resource_type": "Transaction",
            "floor_path": os.path.join(REFS, "floor_transfer_small_sdd.cedar"),
        },
        {
            "name": "floor_transfer_mid_cdd",
            "description": (
                "A CDD customer MUST be permitted a mid-band transfer "
                "(10000 <= amount <= 100000)"
            ),
            "type": "floor",
            "principal_type": "BankCustomer",
            "action": 'Action::"transferOut"',
            "resource_type": "Transaction",
            "floor_path": os.path.join(REFS, "floor_transfer_mid_cdd.cedar"),
        },
        {
            "name": "floor_transfer_large_edd",
            "description": (
                "An EDD customer with uboVerified + adverseMediaClean MUST "
                "be permitted a large transfer (amount > 100000)"
            ),
            "type": "floor",
            "principal_type": "BankCustomer",
            "action": 'Action::"transferOut"',
            "resource_type": "Transaction",
            "floor_path": os.path.join(REFS, "floor_transfer_large_edd.cedar"),
        },
        {
            "name": "floor_open_product_high_risk_edd",
            "description": (
                "A high-risk (riskScore > 70) EDD customer with full "
                "attestations MUST be permitted to open a product"
            ),
            "type": "floor",
            "principal_type": "BankCustomer",
            "action": 'Action::"openProduct"',
            "resource_type": "BankCustomer",
            "floor_path": os.path.join(
                REFS, "floor_open_product_high_risk_edd.cedar"
            ),
        },
        {
            "name": "floor_open_product_standard_cdd",
            "description": (
                "A standard-risk (riskScore <= 70) CDD customer MUST be "
                "permitted to open a product"
            ),
            "type": "floor",
            "principal_type": "BankCustomer",
            "action": 'Action::"openProduct"',
            "resource_type": "BankCustomer",
            "floor_path": os.path.join(
                REFS, "floor_open_product_standard_cdd.cedar"
            ),
        },
        {
            "name": "floor_escalate_review_cdd",
            "description": (
                "A CDD customer MUST be permitted to file a compliance "
                "escalation"
            ),
            "type": "floor",
            "principal_type": "BankCustomer",
            "action": 'Action::"escalateReview"',
            "resource_type": "BankCustomer",
            "floor_path": os.path.join(
                REFS, "floor_escalate_review_cdd.cedar"
            ),
        },

        # -- Liveness ---------------------------------------------------------
        {
            "name": "liveness_view_account",
            "description": "BankCustomer+viewAccount+BankCustomer liveness",
            "type": "always-denies-liveness",
            "principal_type": "BankCustomer",
            "action": 'Action::"viewAccount"',
            "resource_type": "BankCustomer",
        },
        {
            "name": "liveness_transfer_out",
            "description": "BankCustomer+transferOut+Transaction liveness",
            "type": "always-denies-liveness",
            "principal_type": "BankCustomer",
            "action": 'Action::"transferOut"',
            "resource_type": "Transaction",
        },
        {
            "name": "liveness_open_product",
            "description": "BankCustomer+openProduct+BankCustomer liveness",
            "type": "always-denies-liveness",
            "principal_type": "BankCustomer",
            "action": 'Action::"openProduct"',
            "resource_type": "BankCustomer",
        },
        {
            "name": "liveness_escalate_review",
            "description": "BankCustomer+escalateReview+BankCustomer liveness",
            "type": "always-denies-liveness",
            "principal_type": "BankCustomer",
            "action": 'Action::"escalateReview"',
            "resource_type": "BankCustomer",
        },
    ]
