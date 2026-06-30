"""Hand-authored verification plan for realworld/nested_namespaces.

Exercises Cedar's multi-level namespace support. All types are qualified
with multi-segment namespaces:
  - Principal: Company::Identity::Employee
  - Resource:  Company::Billing::Invoice::Line
  - Actions:   Company::Billing::Invoice::Action::"view" | "approve" | "void"

Hunts failure modes:
  - Policies that fail to qualify types in rule heads or action names
  - Policies that hard-code a single namespace prefix everywhere
  - Policies that collapse Tier 1 / Tier 2 approval into one clause and
    lose the amount-bound distinction
  - Planner references unable to reach across namespaces
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")

PRINCIPAL_TYPE = "Company::Identity::Employee"
RESOURCE_TYPE = "Company::Billing::Invoice::Line"
ACTION_VIEW = 'Company::Billing::Invoice::Action::"view"'
ACTION_APPROVE = 'Company::Billing::Invoice::Action::"approve"'
ACTION_VOID = 'Company::Billing::Invoice::Action::"void"'


def get_checks():
    return [
        # ── Safety ceilings ──────────────────────────────────────────────
        {
            "name": "view_safety",
            "description": "view permitted only when (issuer OR owning-team manager OR same dept as issuer)",
            "type": "implies",
            "principal_type": PRINCIPAL_TYPE,
            "action": ACTION_VIEW,
            "resource_type": RESOURCE_TYPE,
            "reference_path": os.path.join(REFS, "view_safety.cedar"),
        },
        {
            "name": "approve_safety",
            "description": "approve permitted only under Tier 1 (team manager L3, <=10k) or Tier 2 (L5, <=100k)",
            "type": "implies",
            "principal_type": PRINCIPAL_TYPE,
            "action": ACTION_APPROVE,
            "resource_type": RESOURCE_TYPE,
            "reference_path": os.path.join(REFS, "approve_safety.cedar"),
        },
        {
            "name": "void_safety",
            "description": "void permitted only when team manager AND level >= 5",
            "type": "implies",
            "principal_type": PRINCIPAL_TYPE,
            "action": ACTION_VOID,
            "resource_type": RESOURCE_TYPE,
            "reference_path": os.path.join(REFS, "void_safety.cedar"),
        },

        # ── Floors ───────────────────────────────────────────────────────
        {
            "name": "issuer_must_view",
            "description": "Issuer MUST be permitted to view their own line",
            "type": "floor",
            "principal_type": PRINCIPAL_TYPE,
            "action": ACTION_VIEW,
            "resource_type": RESOURCE_TYPE,
            "floor_path": os.path.join(REFS, "issuer_must_view.cedar"),
        },
        {
            "name": "manager_must_view",
            "description": "Owning-team manager MUST be permitted to view",
            "type": "floor",
            "principal_type": PRINCIPAL_TYPE,
            "action": ACTION_VIEW,
            "resource_type": RESOURCE_TYPE,
            "floor_path": os.path.join(REFS, "manager_must_view.cedar"),
        },
        {
            "name": "manager_tier1_must_approve",
            "description": "Team manager L3+ MUST be permitted to approve lines <= 10000",
            "type": "floor",
            "principal_type": PRINCIPAL_TYPE,
            "action": ACTION_APPROVE,
            "resource_type": RESOURCE_TYPE,
            "floor_path": os.path.join(REFS, "manager_tier1_must_approve.cedar"),
        },
        {
            "name": "senior_manager_must_void",
            "description": "Level-5+ team manager MUST be permitted to void a line on their own team",
            "type": "floor",
            "principal_type": PRINCIPAL_TYPE,
            "action": ACTION_VOID,
            "resource_type": RESOURCE_TYPE,
            "floor_path": os.path.join(REFS, "senior_manager_must_void.cedar"),
        },

        # ── Liveness ─────────────────────────────────────────────────────
        {
            "name": "liveness_view",
            "description": "Employee+view+Line liveness",
            "type": "always-denies-liveness",
            "principal_type": PRINCIPAL_TYPE,
            "action": ACTION_VIEW,
            "resource_type": RESOURCE_TYPE,
        },
        {
            "name": "liveness_approve",
            "description": "Employee+approve+Line liveness",
            "type": "always-denies-liveness",
            "principal_type": PRINCIPAL_TYPE,
            "action": ACTION_APPROVE,
            "resource_type": RESOURCE_TYPE,
        },
        {
            "name": "liveness_void",
            "description": "Employee+void+Line liveness",
            "type": "always-denies-liveness",
            "principal_type": PRINCIPAL_TYPE,
            "action": ACTION_VOID,
            "resource_type": RESOURCE_TYPE,
        },
    ]
