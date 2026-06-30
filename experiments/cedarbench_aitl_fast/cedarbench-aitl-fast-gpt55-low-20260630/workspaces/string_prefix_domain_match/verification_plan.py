"""Hand-authored verification plan for realworld/string_prefix_domain_match.

Hunts for a harness gap in Cedar string-method feedback. Cedar's only
string-matching primitive is the `like` operator with glob wildcards
(`*`, `?`). It does NOT support `.startsWith()`, `.endsWith()`, or
`.contains()`. LLMs reach for these methods by default because every
other language has them, and Cedar rejects with a clean error
(`"startsWith" is not a valid method`) — but the harness's validation
feedback may not surface the `like` alternative.

This scenario is structurally analogous to the §8.9 duration syntax
trap: non-standard syntax where the LLM's default is wrong. If Haiku
stalls here, the fix is a new detection branch in
_format_validation_feedback or _format_syntax_feedback that catches
"X is not a valid method" on String-typed expressions and emits a
CORRECT/WRONG template pointing at `like`.
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # ── Safety ceilings ──────────────────────────────────────────────
        {"name": "public_read_safety", "description": "readResource permitted only when (public OR internal+employee OR partner+partner-subdomain)", "type": "implies", "principal_type": "User", "action": "Action::\"readResource\"", "resource_type": "Resource", "reference_path": os.path.join(REFS, "public_read_safety.cedar")},
        {"name": "admin_write_safety", "description": "writeResource permitted only when email starts with 'admin@'", "type": "implies", "principal_type": "User", "action": "Action::\"writeResource\"", "resource_type": "Resource", "reference_path": os.path.join(REFS, "admin_write_safety.cedar")},

        # ── Floors ───────────────────────────────────────────────────────
        {"name": "any_must_read_public", "description": "Any User MUST read a public resource", "type": "floor", "principal_type": "User", "action": "Action::\"readResource\"", "resource_type": "Resource", "floor_path": os.path.join(REFS, "any_must_read_public.cedar")},
        {"name": "employee_must_read_internal", "description": "User with @example.com email MUST read internal resources", "type": "floor", "principal_type": "User", "action": "Action::\"readResource\"", "resource_type": "Resource", "floor_path": os.path.join(REFS, "employee_must_read_internal.cedar")},
        {"name": "partner_must_read_partner", "description": "User with @partner.example.com email MUST read partner resources", "type": "floor", "principal_type": "User", "action": "Action::\"readResource\"", "resource_type": "Resource", "floor_path": os.path.join(REFS, "partner_must_read_partner.cedar")},
        {"name": "admin_must_write_any", "description": "User with admin@ email prefix MUST write any resource", "type": "floor", "principal_type": "User", "action": "Action::\"writeResource\"", "resource_type": "Resource", "floor_path": os.path.join(REFS, "admin_must_write_any.cedar")},

        # ── Liveness ─────────────────────────────────────────────────────
        {"name": "liveness_read", "description": "User+readResource+Resource liveness", "type": "always-denies-liveness", "principal_type": "User", "action": "Action::\"readResource\"", "resource_type": "Resource"},
        {"name": "liveness_write", "description": "User+writeResource+Resource liveness", "type": "always-denies-liveness", "principal_type": "User", "action": "Action::\"writeResource\"", "resource_type": "Resource"},
    ]
