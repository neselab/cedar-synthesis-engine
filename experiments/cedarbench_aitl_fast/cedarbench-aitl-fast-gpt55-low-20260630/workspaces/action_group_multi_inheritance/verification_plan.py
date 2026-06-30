"""Verification plan for realworld/action_group_multi_inheritance.

DocumentVault uses Cedar action groups (ReadOnly, AuditLogged, Destructive)
where each concrete action inherits from one or more groups, and each
parent group encodes an independent capability requirement that composes
by conjunction.

Concrete actions:
  Search  : ReadOnly
  View    : ReadOnly + AuditLogged
  Edit    : AuditLogged
  Delete  : AuditLogged + Destructive

Group requirements:
  ReadOnly    : (none)
  AuditLogged : principal.auditCleared
  Destructive : principal.role == "admin"
"""
import os
REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")

def get_checks():
    return [
        # Ceilings: candidate must be no more permissive than reference.
        {"name": "ceiling_search", "description": "Search permitted only as ReadOnly group allows (any user)",
         "type": "implies", "principal_type": "User", "action": 'Action::"Search"', "resource_type": "Document",
         "reference_path": os.path.join(REFS, "ceiling_search.cedar")},
        {"name": "ceiling_view", "description": "View requires auditCleared (AuditLogged requirement)",
         "type": "implies", "principal_type": "User", "action": 'Action::"View"', "resource_type": "Document",
         "reference_path": os.path.join(REFS, "ceiling_view.cedar")},
        {"name": "ceiling_edit", "description": "Edit requires auditCleared (AuditLogged requirement)",
         "type": "implies", "principal_type": "User", "action": 'Action::"Edit"', "resource_type": "Document",
         "reference_path": os.path.join(REFS, "ceiling_edit.cedar")},
        {"name": "ceiling_delete", "description": "Delete requires auditCleared AND admin role (AuditLogged + Destructive)",
         "type": "implies", "principal_type": "User", "action": 'Action::"Delete"', "resource_type": "Document",
         "reference_path": os.path.join(REFS, "ceiling_delete.cedar")},

        # Floors: candidate must be at least as permissive as reference.
        {"name": "floor_search", "description": "any user MUST be able to Search",
         "type": "floor", "principal_type": "User", "action": 'Action::"Search"', "resource_type": "Document",
         "floor_path": os.path.join(REFS, "floor_search.cedar")},
        {"name": "floor_view", "description": "audit-cleared user MUST be able to View",
         "type": "floor", "principal_type": "User", "action": 'Action::"View"', "resource_type": "Document",
         "floor_path": os.path.join(REFS, "floor_view.cedar")},
        {"name": "floor_edit", "description": "audit-cleared user MUST be able to Edit",
         "type": "floor", "principal_type": "User", "action": 'Action::"Edit"', "resource_type": "Document",
         "floor_path": os.path.join(REFS, "floor_edit.cedar")},
        {"name": "floor_delete", "description": "audit-cleared admin MUST be able to Delete",
         "type": "floor", "principal_type": "User", "action": 'Action::"Delete"', "resource_type": "Document",
         "floor_path": os.path.join(REFS, "floor_delete.cedar")},

        # Liveness: at least one request permitted per concrete action.
        {"name": "liveness_search", "description": "at least one Search permitted",
         "type": "always-denies-liveness", "principal_type": "User", "action": 'Action::"Search"', "resource_type": "Document"},
        {"name": "liveness_view", "description": "at least one View permitted",
         "type": "always-denies-liveness", "principal_type": "User", "action": 'Action::"View"', "resource_type": "Document"},
        {"name": "liveness_edit", "description": "at least one Edit permitted",
         "type": "always-denies-liveness", "principal_type": "User", "action": 'Action::"Edit"', "resource_type": "Document"},
        {"name": "liveness_delete", "description": "at least one Delete permitted",
         "type": "always-denies-liveness", "principal_type": "User", "action": 'Action::"Delete"', "resource_type": "Document"},
    ]
