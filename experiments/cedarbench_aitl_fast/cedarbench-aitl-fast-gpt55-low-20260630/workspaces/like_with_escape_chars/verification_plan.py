"""Hand-authored verification plan for realworld/like_with_escape_chars.

Hunts for an LLM/harness gap around Cedar's `like` operator escape
syntax. Cedar uses glob-style patterns (not regex), and the escape
for a literal `*` is `\*` (single backslash). LLMs default to regex
conventions (`.*`, `\\*`, `[*]`) — those either fail to parse or
silently behave wrong. LLMs also reach for non-existent string methods
like `.contains()` or `.startsWith()`; Cedar strings have none.

If Haiku stalls here, the fix is a new detection branch in the
syntax/validation feedback layer that surfaces the literal-vs-wildcard
distinction in `like` patterns and points at the `\*` escape.
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # ── Safety ceilings ──────────────────────────────────────────────
        {
            "name": "read_safety",
            "description": "read permitted only when (docs/* any user) OR (reports/<any>*-final user role) OR (system/* admin)",
            "type": "implies",
            "principal_type": "User",
            "action": "Action::\"read\"",
            "resource_type": "File",
            "reference_path": os.path.join(REFS, "read_safety.cedar"),
        },
        {
            "name": "write_safety",
            "description": "write permitted only for admins on any file",
            "type": "implies",
            "principal_type": "User",
            "action": "Action::\"write\"",
            "resource_type": "File",
            "reference_path": os.path.join(REFS, "write_safety.cedar"),
        },

        # ── Floors ───────────────────────────────────────────────────────
        {
            "name": "any_must_read_docs",
            "description": "Any User MUST read files matching docs/*",
            "type": "floor",
            "principal_type": "User",
            "action": "Action::\"read\"",
            "resource_type": "File",
            "floor_path": os.path.join(REFS, "any_must_read_docs.cedar"),
        },
        {
            "name": "user_must_read_literal_asterisk_reports",
            "description": "role=user MUST read files matching reports/<any>*-final (literal *)",
            "type": "floor",
            "principal_type": "User",
            "action": "Action::\"read\"",
            "resource_type": "File",
            "floor_path": os.path.join(REFS, "user_must_read_literal_asterisk_reports.cedar"),
        },
        {
            "name": "admin_must_read_system",
            "description": "role=admin MUST read files matching system/*",
            "type": "floor",
            "principal_type": "User",
            "action": "Action::\"read\"",
            "resource_type": "File",
            "floor_path": os.path.join(REFS, "admin_must_read_system.cedar"),
        },
        {
            "name": "admin_must_write_any",
            "description": "role=admin MUST write any File",
            "type": "floor",
            "principal_type": "User",
            "action": "Action::\"write\"",
            "resource_type": "File",
            "floor_path": os.path.join(REFS, "admin_must_write_any.cedar"),
        },

        # ── Liveness ─────────────────────────────────────────────────────
        {
            "name": "liveness_read",
            "description": "User+read+File liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": "Action::\"read\"",
            "resource_type": "File",
        },
        {
            "name": "liveness_write",
            "description": "User+write+File liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": "Action::\"write\"",
            "resource_type": "File",
        },
    ]
