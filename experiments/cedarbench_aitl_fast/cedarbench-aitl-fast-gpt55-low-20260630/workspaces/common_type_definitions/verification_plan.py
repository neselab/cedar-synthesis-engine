"""Hand-authored verification plan for realworld/common_type_definitions.

Exercises Cedar's `type X = ...` schema feature (common type definitions).
The schema declares two common types:
  - Address    = { street, zip, country }
  - ContactInfo = { email, phone, address: Address }
and shares ContactInfo across three entity types (Customer, Vendor,
Employee).

Hunts failure modes:
  - Synthesizer inlines record types instead of using the named alias.
    (Cedar accepts both, but inlining defeats the test of whether the
     model groks the common-type indirection in the schema.)
  - Wrong nested-access path. The country lives at
    resource.contact.address.country — a 3-deep chain through two
    common-type aliases. Synthesizers may flatten to
    resource.address.country or resource.country.
  - Missing admin override on viewContact (admin should see all).
  - Admin override leaks onto updateContact (it should NOT — only the
    owner updates their own contact).
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")

ACTION_VIEW = 'Action::"viewContact"'
ACTION_UPDATE = 'Action::"updateContact"'
ACTION_VERIFY = 'Action::"verifyAddress"'


def get_checks():
    return [
        # ── Safety ceilings ──────────────────────────────────────────────
        {
            "name": "view_safety_customer_principal",
            "description": "When principal is Customer, viewContact permitted only for own record (principal == resource).",
            "type": "implies",
            "principal_type": "Customer",
            "action": ACTION_VIEW,
            "resource_type": "Customer",
            "reference_path": os.path.join(REFS, "view_safety_customer_principal.cedar"),
        },
        {
            "name": "view_safety_admin_principal",
            "description": "When principal is Admin, viewContact is broadly permitted (admin override).",
            "type": "implies",
            "principal_type": "Admin",
            "action": ACTION_VIEW,
            "resource_type": "Customer",
            "reference_path": os.path.join(REFS, "view_safety_admin_principal.cedar"),
        },
        {
            "name": "update_safety_customer",
            "description": "Customers may update contact ONLY for their own record (no admin override on update).",
            "type": "implies",
            "principal_type": "Customer",
            "action": ACTION_UPDATE,
            "resource_type": "Customer",
            "reference_path": os.path.join(REFS, "update_safety_customer.cedar"),
        },
        {
            "name": "verify_safety_admin",
            "description": "verifyAddress permitted only when resource.contact.address.country == \"US\".",
            "type": "implies",
            "principal_type": "Admin",
            "action": ACTION_VERIFY,
            "resource_type": "Customer",
            "reference_path": os.path.join(REFS, "verify_safety_admin.cedar"),
        },

        # ── Floors ───────────────────────────────────────────────────────
        {
            "name": "floor_customer_self_view",
            "description": "Customer MUST be permitted to view own contact.",
            "type": "floor",
            "principal_type": "Customer",
            "action": ACTION_VIEW,
            "resource_type": "Customer",
            "floor_path": os.path.join(REFS, "floor_customer_self_view.cedar"),
        },
        {
            "name": "floor_employee_self_view",
            "description": "Employee MUST be permitted to view own contact.",
            "type": "floor",
            "principal_type": "Employee",
            "action": ACTION_VIEW,
            "resource_type": "Employee",
            "floor_path": os.path.join(REFS, "floor_employee_self_view.cedar"),
        },
        {
            "name": "floor_admin_view_customer",
            "description": "Admin MUST be permitted to view any Customer's contact.",
            "type": "floor",
            "principal_type": "Admin",
            "action": ACTION_VIEW,
            "resource_type": "Customer",
            "floor_path": os.path.join(REFS, "floor_admin_view_customer.cedar"),
        },
        {
            "name": "floor_customer_self_update",
            "description": "Customer MUST be permitted to update own contact.",
            "type": "floor",
            "principal_type": "Customer",
            "action": ACTION_UPDATE,
            "resource_type": "Customer",
            "floor_path": os.path.join(REFS, "floor_customer_self_update.cedar"),
        },
        {
            "name": "floor_admin_verify_us",
            "description": "Admin MUST be permitted to verify a Customer with country == \"US\".",
            "type": "floor",
            "principal_type": "Admin",
            "action": ACTION_VERIFY,
            "resource_type": "Customer",
            "floor_path": os.path.join(REFS, "floor_admin_verify_us.cedar"),
        },

        # ── Liveness ─────────────────────────────────────────────────────
        {
            "name": "liveness_view",
            "description": "viewContact must permit at least one request.",
            "type": "always-denies-liveness",
            "principal_type": "Customer",
            "action": ACTION_VIEW,
            "resource_type": "Customer",
        },
        {
            "name": "liveness_update",
            "description": "updateContact must permit at least one request.",
            "type": "always-denies-liveness",
            "principal_type": "Customer",
            "action": ACTION_UPDATE,
            "resource_type": "Customer",
        },
        {
            "name": "liveness_verify",
            "description": "verifyAddress must permit at least one request.",
            "type": "always-denies-liveness",
            "principal_type": "Admin",
            "action": ACTION_VERIFY,
            "resource_type": "Customer",
        },
    ]
