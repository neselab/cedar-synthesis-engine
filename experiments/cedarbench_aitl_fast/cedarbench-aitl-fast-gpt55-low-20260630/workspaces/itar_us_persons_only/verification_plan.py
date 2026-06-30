"""Hand-authored verification plan for realworld/itar_us_persons_only.

ITAR / EAR export-control pattern. Models the "deemed export" rule:
controlled technical data may be released only to "US persons" (US
citizens or LPRs). Three actions of increasing strictness — view,
download (location-gated for ITAR), export (US persons only, cleared,
domestic).

Tests:
  - Single-valued string-enum citizenshipStatus encoded as explicit
    disjunction `== "US_CITIZEN" || == "LPR"` (Cedar has no enum
    ordering and no `in` over string literals).
  - Action variants of progressively stricter requirements.
  - Context-based deemed-export check (accessLocation).
  - Controlled vs uncontrolled data dichotomy gating non-US persons.
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # ── Safety ceilings ──────────────────────────────────────────────
        {"name": "view_safety", "description": "view permitted only when principal is a US person OR data is uncontrolled (EAR99 + not ITAR)", "type": "implies", "principal_type": "Engineer", "action": "Action::\"view\"", "resource_type": "TechnicalData", "reference_path": os.path.join(REFS, "view_safety.cedar")},
        {"name": "download_safety", "description": "download permitted only when (US person OR uncontrolled) AND (not ITAR OR accessLocation == US)", "type": "implies", "principal_type": "Engineer", "action": "Action::\"download\"", "resource_type": "TechnicalData", "reference_path": os.path.join(REFS, "download_safety.cedar")},
        {"name": "export_safety", "description": "export permitted only when US person AND clearanceVerified AND accessLocation == US", "type": "implies", "principal_type": "Engineer", "action": "Action::\"export\"", "resource_type": "TechnicalData", "reference_path": os.path.join(REFS, "export_safety.cedar")},

        # ── Floors ───────────────────────────────────────────────────────
        {"name": "us_citizen_must_view_itar", "description": "US citizen MUST view ITAR-controlled data (no location restriction on view)", "type": "floor", "principal_type": "Engineer", "action": "Action::\"view\"", "resource_type": "TechnicalData", "floor_path": os.path.join(REFS, "us_citizen_must_view_itar.cedar")},
        {"name": "non_us_must_view_ear99", "description": "NON_US engineer MUST view uncontrolled (EAR99, non-ITAR) data", "type": "floor", "principal_type": "Engineer", "action": "Action::\"view\"", "resource_type": "TechnicalData", "floor_path": os.path.join(REFS, "non_us_must_view_ear99.cedar")},
        {"name": "lpr_must_download_itar_in_us", "description": "LPR engineer accessing from US MUST download ITAR data", "type": "floor", "principal_type": "Engineer", "action": "Action::\"download\"", "resource_type": "TechnicalData", "floor_path": os.path.join(REFS, "lpr_must_download_itar_in_us.cedar")},
        {"name": "visa_must_download_ear99", "description": "VISA engineer MUST download EAR99 (uncontrolled) data, any location", "type": "floor", "principal_type": "Engineer", "action": "Action::\"download\"", "resource_type": "TechnicalData", "floor_path": os.path.join(REFS, "visa_must_download_ear99.cedar")},
        {"name": "cleared_us_citizen_must_export", "description": "US citizen with clearanceVerified, accessing from US, MUST export", "type": "floor", "principal_type": "Engineer", "action": "Action::\"export\"", "resource_type": "TechnicalData", "floor_path": os.path.join(REFS, "cleared_us_citizen_must_export.cedar")},

        # ── Liveness ─────────────────────────────────────────────────────
        {"name": "liveness_view", "description": "Engineer+view+TechnicalData liveness", "type": "always-denies-liveness", "principal_type": "Engineer", "action": "Action::\"view\"", "resource_type": "TechnicalData"},
        {"name": "liveness_download", "description": "Engineer+download+TechnicalData liveness", "type": "always-denies-liveness", "principal_type": "Engineer", "action": "Action::\"download\"", "resource_type": "TechnicalData"},
        {"name": "liveness_export", "description": "Engineer+export+TechnicalData liveness", "type": "always-denies-liveness", "principal_type": "Engineer", "action": "Action::\"export\"", "resource_type": "TechnicalData"},
    ]
