"""Hand-authored verification plan for realworld/regression_battery_all_traps.

Single scenario engineered to exercise every documented harness
contribution. If any one of §8.1, §8.4, §8.6, §8.8, §8.9, §8.11
regresses, this scenario fails.

  3 ceilings (read, edit, archive)
+ 6 floors   (covering both time directions, multi-role users,
              optional MFA present and absent, post-expiry archive)
+ 3 liveness (read, edit, archive)
= 12 checks total.

Per-trigger summary:
  §8.1  — read/edit ceilings tighten pre-expiry; archive ceiling +
          archive floor loosen post-expiry. Diagnostics that conflate
          implies-direction with floor-direction will misroute.
  §8.4  — read_ceiling, floor_contractor_with_mfa_read_confidential
          read context.mfaToken (must be has-guarded);
          floor_manager_read_confidential_no_mfa NEVER reads it
          (must permit without touching the optional attribute).
  §8.6  — floor_contractor_with_secondary_manager_edit lands a
          witness with primaryRole=="contractor" AND
          secondaryRoles.contains("manager"). Any candidate that
          encodes the contractor restriction as
            forbid when primaryRole == "contractor"
          fails this floor.
  §8.8  — every floor includes !principal.isBlocked, mirroring the
          global "blocked users denied" forbid the candidate is
          expected to write. Floors that ignore the global forbid
          are unsatisfiable jointly with it.
  §8.9  — every reference uses Go-style duration via
          context.graceWindow (a duration). A candidate that emits
          duration("PT21H") (ISO 8601) is rejected at parse time.
  §8.11 — the classification-and-MFA gate in read_ceiling is the
          natural ?: candidate. The candidate must express it with
          boolean disjunction, and floor_manager_read_confidential_no_mfa
          catches the common ternary mistake of accidentally
          requiring MFA for managers.
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # ── Safety ceilings (one per action) ───────────────────────────────
        {"name": "read_ceiling", "description": "read permitted only when not blocked, before (graced) expiry, and the role-and-MFA gate matches the classification (admin/manager always; contractor on confidential needs MFA)", "type": "implies", "principal_type": "User", "action": "Action::\"read\"", "resource_type": "Document", "reference_path": os.path.join(REFS, "read_ceiling.cedar")},
        {"name": "edit_ceiling", "description": "edit permitted only when not blocked, before (graced) expiry, and the user is in role admin or manager (primary or secondary)", "type": "implies", "principal_type": "User", "action": "Action::\"edit\"", "resource_type": "Document", "reference_path": os.path.join(REFS, "edit_ceiling.cedar")},
        {"name": "archive_ceiling", "description": "archive permitted only when not blocked, AFTER expiry (no grace), and the user is in role admin (primary or secondary)", "type": "implies", "principal_type": "User", "action": "Action::\"archive\"", "resource_type": "Document", "reference_path": os.path.join(REFS, "archive_ceiling.cedar")},

        # ── Floors (positive obligations) ──────────────────────────────────
        {"name": "floor_admin_read_public", "description": "non-blocked admin MUST read a public document before (graced) expiry", "type": "floor", "principal_type": "User", "action": "Action::\"read\"", "resource_type": "Document", "floor_path": os.path.join(REFS, "floor_admin_read_public.cedar")},
        {"name": "floor_manager_read_confidential_no_mfa", "description": "non-blocked manager MUST read a confidential document before (graced) expiry, even with no mfaToken in context — exercises §8.4 and §8.11", "type": "floor", "principal_type": "User", "action": "Action::\"read\"", "resource_type": "Document", "floor_path": os.path.join(REFS, "floor_manager_read_confidential_no_mfa.cedar")},
        {"name": "floor_contractor_with_mfa_read_confidential", "description": "non-blocked contractor with fresh MFA MUST read a confidential document before (graced) expiry — has-guarded mfaToken", "type": "floor", "principal_type": "User", "action": "Action::\"read\"", "resource_type": "Document", "floor_path": os.path.join(REFS, "floor_contractor_with_mfa_read_confidential.cedar")},
        {"name": "floor_manager_edit", "description": "non-blocked manager MUST edit a document before (graced) expiry", "type": "floor", "principal_type": "User", "action": "Action::\"edit\"", "resource_type": "Document", "floor_path": os.path.join(REFS, "floor_manager_edit.cedar")},
        {"name": "floor_contractor_with_secondary_manager_edit", "description": "non-blocked user with primaryRole=='contractor' AND 'manager' in secondaryRoles MUST edit — direct §8.6 role-intersection trap", "type": "floor", "principal_type": "User", "action": "Action::\"edit\"", "resource_type": "Document", "floor_path": os.path.join(REFS, "floor_contractor_with_secondary_manager_edit.cedar")},
        {"name": "floor_admin_archive_after_expiry", "description": "non-blocked admin MUST archive a document AFTER expiry — opposite time direction from read/edit floors (§8.1)", "type": "floor", "principal_type": "User", "action": "Action::\"archive\"", "resource_type": "Document", "floor_path": os.path.join(REFS, "floor_admin_archive_after_expiry.cedar")},

        # ── Liveness (one per action) ──────────────────────────────────────
        {"name": "liveness_read", "description": "User+read+Document liveness", "type": "always-denies-liveness", "principal_type": "User", "action": "Action::\"read\"", "resource_type": "Document"},
        {"name": "liveness_edit", "description": "User+edit+Document liveness", "type": "always-denies-liveness", "principal_type": "User", "action": "Action::\"edit\"", "resource_type": "Document"},
        {"name": "liveness_archive", "description": "User+archive+Document liveness", "type": "always-denies-liveness", "principal_type": "User", "action": "Action::\"archive\"", "resource_type": "Document"},
    ]
