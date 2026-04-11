"""Hand-authored verification plan for realworld/api_key_scoped_access.

Machine-to-machine authorization via API keys. Tests:
  - Non-User principal type (ApiKey)
  - Scope-to-action mapping via set string membership
  - Expiry + revocation composition (two separate global forbids)
  - Submitted-invoice immutability (conditional forbid on one action)
  - Organization-level tenant isolation
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # ── Safety ceilings (one per action) ─────────────────────────────
        {"name": "read_document_safety", "description": "readDocument permitted only when (same org, read:document scope, not expired, not revoked)", "type": "implies", "principal_type": "ApiKey", "action": "Action::\"readDocument\"", "resource_type": "Document", "reference_path": os.path.join(REFS, "read_document_safety.cedar")},
        {"name": "write_document_safety", "description": "writeDocument permitted only when (same org, write:document scope, not expired, not revoked)", "type": "implies", "principal_type": "ApiKey", "action": "Action::\"writeDocument\"", "resource_type": "Document", "reference_path": os.path.join(REFS, "write_document_safety.cedar")},
        {"name": "delete_document_safety", "description": "deleteDocument permitted only when (same org, delete:document scope, not expired, not revoked)", "type": "implies", "principal_type": "ApiKey", "action": "Action::\"deleteDocument\"", "resource_type": "Document", "reference_path": os.path.join(REFS, "delete_document_safety.cedar")},
        {"name": "read_invoice_safety", "description": "readInvoice permitted only when (same org, read:invoice scope, not expired, not revoked)", "type": "implies", "principal_type": "ApiKey", "action": "Action::\"readInvoice\"", "resource_type": "Invoice", "reference_path": os.path.join(REFS, "read_invoice_safety.cedar")},
        {"name": "write_invoice_safety", "description": "writeInvoice permitted only when (same org, write:invoice scope, not expired, not revoked, NOT submitted)", "type": "implies", "principal_type": "ApiKey", "action": "Action::\"writeInvoice\"", "resource_type": "Invoice", "reference_path": os.path.join(REFS, "write_invoice_safety.cedar")},

        # ── Floors ───────────────────────────────────────────────────────
        {"name": "valid_key_must_read_document", "description": "Active key with read:document scope MUST read a document in same org", "type": "floor", "principal_type": "ApiKey", "action": "Action::\"readDocument\"", "resource_type": "Document", "floor_path": os.path.join(REFS, "valid_key_must_read_document.cedar")},
        {"name": "valid_key_must_write_document", "description": "Active key with write:document scope MUST write a document in same org", "type": "floor", "principal_type": "ApiKey", "action": "Action::\"writeDocument\"", "resource_type": "Document", "floor_path": os.path.join(REFS, "valid_key_must_write_document.cedar")},
        {"name": "valid_key_must_read_unsubmitted_invoice", "description": "Active key with read:invoice scope MUST read an invoice in same org", "type": "floor", "principal_type": "ApiKey", "action": "Action::\"readInvoice\"", "resource_type": "Invoice", "floor_path": os.path.join(REFS, "valid_key_must_read_unsubmitted_invoice.cedar")},
        {"name": "valid_key_must_write_unsubmitted_invoice", "description": "Active key with write:invoice scope MUST write an UNSUBMITTED invoice in same org", "type": "floor", "principal_type": "ApiKey", "action": "Action::\"writeInvoice\"", "resource_type": "Invoice", "floor_path": os.path.join(REFS, "valid_key_must_write_unsubmitted_invoice.cedar")},

        # ── Liveness ─────────────────────────────────────────────────────
        {"name": "liveness_read_document", "description": "ApiKey+readDocument+Document liveness", "type": "always-denies-liveness", "principal_type": "ApiKey", "action": "Action::\"readDocument\"", "resource_type": "Document"},
        {"name": "liveness_write_document", "description": "ApiKey+writeDocument+Document liveness", "type": "always-denies-liveness", "principal_type": "ApiKey", "action": "Action::\"writeDocument\"", "resource_type": "Document"},
        {"name": "liveness_delete_document", "description": "ApiKey+deleteDocument+Document liveness", "type": "always-denies-liveness", "principal_type": "ApiKey", "action": "Action::\"deleteDocument\"", "resource_type": "Document"},
        {"name": "liveness_read_invoice", "description": "ApiKey+readInvoice+Invoice liveness", "type": "always-denies-liveness", "principal_type": "ApiKey", "action": "Action::\"readInvoice\"", "resource_type": "Invoice"},
        {"name": "liveness_write_invoice", "description": "ApiKey+writeInvoice+Invoice liveness", "type": "always-denies-liveness", "principal_type": "ApiKey", "action": "Action::\"writeInvoice\"", "resource_type": "Invoice"},
    ]
