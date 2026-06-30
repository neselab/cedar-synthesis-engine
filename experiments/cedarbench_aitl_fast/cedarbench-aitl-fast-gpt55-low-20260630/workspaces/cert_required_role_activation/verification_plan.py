"""Hand-authored verification plan for realworld/cert_required_role_activation.

Certificate-gated role activation. An operator's privileges depend
on EITHER their long-lived `baseRole` OR a short-lived signed
certificate presented in the request context. Tests:
  - Optional record-typed context attribute (`cert?: { ... }`).
  - Triple has-guard chain on optional record fields (§8.3): every
    read of `context.cert.<field>` must be preceded by a
    `context has cert` guard in the same conjunction.
  - Disjunction across two qualifying conditions (base role OR cert).
  - String equality on a trusted-CA signer.
  - Datetime comparison against issued credential expiry.

Hunts for the failure modes where the model:
  (a) reads `context.cert.<field>` without a `context has cert`
      guard (schema-validation failure),
  (b) accepts any signer instead of `"trusted-ca"` only,
  (c) accepts a `claimedRole` other than `"admin"`,
  (d) drops the disjunction and forces every operator to present a
      cert (breaks `base_admin_executeadmin_must_permit`),
  (e) gates `view` on the cert (breaks `view_user_must_permit`).
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # -- Safety ceilings --------------------------------------------------
        {
            "name": "view_safety",
            "description": (
                "view permitted only when baseRole is 'user' or 'admin' "
                "(guests excluded); cert is not consulted for view"
            ),
            "type": "implies",
            "principal_type": "Operator",
            "action": 'Action::"view"',
            "resource_type": "Resource",
            "reference_path": os.path.join(REFS, "view_safety.cedar"),
        },
        {
            "name": "execute_admin_safety",
            "description": (
                "executeAdmin permitted only when baseRole == 'admin' OR "
                "(cert present AND cert.validUntil > now AND "
                "cert.claimedRole == 'admin' AND cert.signer == 'trusted-ca')"
            ),
            "type": "implies",
            "principal_type": "Operator",
            "action": 'Action::"executeAdmin"',
            "resource_type": "Resource",
            "reference_path": os.path.join(REFS, "execute_admin_safety.cedar"),
        },

        # -- Floors -----------------------------------------------------------
        {
            "name": "view_user_must_permit",
            "description": "operator with baseRole 'user' MUST be able to view",
            "type": "floor",
            "principal_type": "Operator",
            "action": 'Action::"view"',
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, "view_user_must_permit.cedar"),
        },
        {
            "name": "view_admin_must_permit",
            "description": "operator with baseRole 'admin' MUST be able to view",
            "type": "floor",
            "principal_type": "Operator",
            "action": 'Action::"view"',
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, "view_admin_must_permit.cedar"),
        },
        {
            "name": "base_admin_executeadmin_must_permit",
            "description": (
                "operator with baseRole 'admin' MUST be able to executeAdmin "
                "without presenting a certificate"
            ),
            "type": "floor",
            "principal_type": "Operator",
            "action": 'Action::"executeAdmin"',
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, "base_admin_executeadmin_must_permit.cedar"),
        },
        {
            "name": "cert_elevated_executeadmin_must_permit",
            "description": (
                "operator presenting a valid, unexpired admin-claiming cert "
                "signed by trusted-ca MUST be permitted to executeAdmin"
            ),
            "type": "floor",
            "principal_type": "Operator",
            "action": 'Action::"executeAdmin"',
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, "cert_elevated_executeadmin_must_permit.cedar"),
        },

        # -- Liveness ---------------------------------------------------------
        {
            "name": "liveness_view",
            "description": "Operator+view+Resource liveness",
            "type": "always-denies-liveness",
            "principal_type": "Operator",
            "action": 'Action::"view"',
            "resource_type": "Resource",
        },
        {
            "name": "liveness_execute_admin",
            "description": "Operator+executeAdmin+Resource liveness",
            "type": "always-denies-liveness",
            "principal_type": "Operator",
            "action": 'Action::"executeAdmin"',
            "resource_type": "Resource",
        },
    ]
