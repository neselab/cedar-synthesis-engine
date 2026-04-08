"""Hand-authored verification plan for tax_full_expansion.

Stacks all tax mutations:
  - Professional (org match + serviceline + location)
  - Supervisor (supervised_orgs)
  - Auditor (auditScope, viewDocument only)
  - viewDocument + editDocument actions
  - Consent forbid (all principals, all actions)
  - Sensitivity forbid (isSensitive requires "HQ" in team_region_list)

Five safety ceilings (one per principal × action combination) each include
all applicable constraints. Five non-sensitive floors (one per combination)
use `!resource.isSensitive` as the §8.8 exclusion. Five liveness checks.
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # ── Safety ceilings ──────────────────────────────────────────────
        {"name": "professional_view_safety", "description": "Professional may viewDocument only when (org match AND consent AND sensitivity-HQ)", "type": "implies", "principal_type": "Taxpreparer::Professional", "action": "Taxpreparer::Action::\"viewDocument\"", "resource_type": "Taxpreparer::Document", "reference_path": os.path.join(REFS, "professional_view_safety.cedar")},
        {"name": "professional_edit_safety", "description": "Professional may editDocument only when (org match AND consent AND sensitivity-HQ)", "type": "implies", "principal_type": "Taxpreparer::Professional", "action": "Taxpreparer::Action::\"editDocument\"", "resource_type": "Taxpreparer::Document", "reference_path": os.path.join(REFS, "professional_edit_safety.cedar")},
        {"name": "supervisor_view_safety", "description": "Supervisor may viewDocument only when (supervised_orgs AND consent AND sensitivity-HQ)", "type": "implies", "principal_type": "Taxpreparer::Supervisor", "action": "Taxpreparer::Action::\"viewDocument\"", "resource_type": "Taxpreparer::Document", "reference_path": os.path.join(REFS, "supervisor_view_safety.cedar")},
        {"name": "supervisor_edit_safety", "description": "Supervisor may editDocument only when (supervised_orgs AND consent AND sensitivity-HQ)", "type": "implies", "principal_type": "Taxpreparer::Supervisor", "action": "Taxpreparer::Action::\"editDocument\"", "resource_type": "Taxpreparer::Document", "reference_path": os.path.join(REFS, "supervisor_edit_safety.cedar")},
        {"name": "auditor_view_safety", "description": "Auditor may viewDocument only when (auditScope AND consent AND sensitivity-HQ)", "type": "implies", "principal_type": "Taxpreparer::Auditor", "action": "Taxpreparer::Action::\"viewDocument\"", "resource_type": "Taxpreparer::Document", "reference_path": os.path.join(REFS, "auditor_view_safety.cedar")},

        # ── Non-sensitive floors ─────────────────────────────────────────
        {"name": "professional_must_view_non_sensitive", "description": "Professional MUST viewDocument (non-sensitive, org match, consent)", "type": "floor", "principal_type": "Taxpreparer::Professional", "action": "Taxpreparer::Action::\"viewDocument\"", "resource_type": "Taxpreparer::Document", "floor_path": os.path.join(REFS, "professional_must_view_non_sensitive.cedar")},
        {"name": "professional_must_edit_non_sensitive", "description": "Professional MUST editDocument (non-sensitive, org match, consent)", "type": "floor", "principal_type": "Taxpreparer::Professional", "action": "Taxpreparer::Action::\"editDocument\"", "resource_type": "Taxpreparer::Document", "floor_path": os.path.join(REFS, "professional_must_edit_non_sensitive.cedar")},
        {"name": "supervisor_must_view_non_sensitive", "description": "Supervisor MUST viewDocument (non-sensitive, supervised org, consent)", "type": "floor", "principal_type": "Taxpreparer::Supervisor", "action": "Taxpreparer::Action::\"viewDocument\"", "resource_type": "Taxpreparer::Document", "floor_path": os.path.join(REFS, "supervisor_must_view_non_sensitive.cedar")},
        {"name": "supervisor_must_edit_non_sensitive", "description": "Supervisor MUST editDocument (non-sensitive, supervised org, consent)", "type": "floor", "principal_type": "Taxpreparer::Supervisor", "action": "Taxpreparer::Action::\"editDocument\"", "resource_type": "Taxpreparer::Document", "floor_path": os.path.join(REFS, "supervisor_must_edit_non_sensitive.cedar")},
        {"name": "auditor_must_view_non_sensitive", "description": "Auditor MUST viewDocument (non-sensitive, auditScope, consent)", "type": "floor", "principal_type": "Taxpreparer::Auditor", "action": "Taxpreparer::Action::\"viewDocument\"", "resource_type": "Taxpreparer::Document", "floor_path": os.path.join(REFS, "auditor_must_view_non_sensitive.cedar")},

        # ── Liveness ─────────────────────────────────────────────────────
        {"name": "liveness_professional_view", "description": "Professional+viewDocument liveness", "type": "always-denies-liveness", "principal_type": "Taxpreparer::Professional", "action": "Taxpreparer::Action::\"viewDocument\"", "resource_type": "Taxpreparer::Document"},
        {"name": "liveness_professional_edit", "description": "Professional+editDocument liveness", "type": "always-denies-liveness", "principal_type": "Taxpreparer::Professional", "action": "Taxpreparer::Action::\"editDocument\"", "resource_type": "Taxpreparer::Document"},
        {"name": "liveness_supervisor_view", "description": "Supervisor+viewDocument liveness", "type": "always-denies-liveness", "principal_type": "Taxpreparer::Supervisor", "action": "Taxpreparer::Action::\"viewDocument\"", "resource_type": "Taxpreparer::Document"},
        {"name": "liveness_supervisor_edit", "description": "Supervisor+editDocument liveness", "type": "always-denies-liveness", "principal_type": "Taxpreparer::Supervisor", "action": "Taxpreparer::Action::\"editDocument\"", "resource_type": "Taxpreparer::Document"},
        {"name": "liveness_auditor_view", "description": "Auditor+viewDocument liveness", "type": "always-denies-liveness", "principal_type": "Taxpreparer::Auditor", "action": "Taxpreparer::Action::\"viewDocument\"", "resource_type": "Taxpreparer::Document"},
    ]
