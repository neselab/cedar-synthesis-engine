"""Verification plan for five_namespace_coordination."""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        {"name": "viewInvoice_safety", "description": "viewInvoice ceiling", "type": "implies", "principal_type": "Identity::User", "action": 'Billing::Action::"viewInvoice"', "resource_type": "Billing::Invoice", "reference_path": os.path.join(REFS, "viewInvoice_safety.cedar")},
        {"name": "payInvoice_safety", "description": "payInvoice ceiling", "type": "implies", "principal_type": "Identity::User", "action": 'Billing::Action::"payInvoice"', "resource_type": "Billing::Invoice", "reference_path": os.path.join(REFS, "payInvoice_safety.cedar")},
        {"name": "viewProduct_safety", "description": "viewProduct ceiling", "type": "implies", "principal_type": "Identity::User", "action": 'Catalog::Action::"viewProduct"', "resource_type": "Catalog::Product", "reference_path": os.path.join(REFS, "viewProduct_safety.cedar")},
        {"name": "viewAddress_safety", "description": "viewAddress ceiling", "type": "implies", "principal_type": "Identity::User", "action": 'Shipping::Action::"viewAddress"', "resource_type": "Shipping::Address", "reference_path": os.path.join(REFS, "viewAddress_safety.cedar")},
        {"name": "recordEvent_safety", "description": "recordEvent ceiling", "type": "implies", "principal_type": "Identity::User", "action": 'Audit::Action::"recordEvent"', "resource_type": "Audit::Event", "reference_path": os.path.join(REFS, "recordEvent_safety.cedar")},
        {"name": "floor_customer_view_invoice", "description": "customer must view their invoice", "type": "floor", "principal_type": "Identity::User", "action": 'Billing::Action::"viewInvoice"', "resource_type": "Billing::Invoice", "floor_path": os.path.join(REFS, "floor_customer_view_invoice.cedar")},
        {"name": "floor_owner_view_address", "description": "owner must view their address", "type": "floor", "principal_type": "Identity::User", "action": 'Shipping::Action::"viewAddress"', "resource_type": "Shipping::Address", "floor_path": os.path.join(REFS, "floor_owner_view_address.cedar")},
    ]
