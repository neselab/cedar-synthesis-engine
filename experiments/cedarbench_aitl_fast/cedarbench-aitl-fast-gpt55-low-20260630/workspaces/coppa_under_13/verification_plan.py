"""Hand-authored verification plan for realworld/coppa_under_13.

COPPA (Children's Online Privacy Protection Act, 16 CFR Part 312)
gates collection of personal data on children under 13 behind verifiable
parental consent, and forbids third-party disclosure of children's
personal data even with consent (the COPPA-stricter rule for sharing).

Day threshold: 4748 days = conservative leap-year-safe threshold for
"at least 13 years old," matching the convention in
age_verification_leap_years.

Common failure modes this scenario hunts:
  - Candidate forgets the §8.3 has-guard on the optional
    parentalConsentToken context attribute.
  - Candidate writes the negated-has trap
    `!(context has parentalConsentToken) || ...`, which Cedar's
    type-checker rejects.
  - Candidate ages the wrong party for share (uses principal age
    instead of the data subject = resource.owner).
  - Candidate over-permits share by allowing personal data sharing
    for under-13 users when consent is present (the COPPA-stricter
    rule forbids this regardless of consent).
  - Candidate uses naive years*365 conversion or expression-argument
    duration() (rejected by Cedar — duration() takes a string literal).
  - Candidate forgets that parental consent ONLY enables collection,
    not sharing, of children's personal data.

11 checks total (3 ceilings + 5 floors + 3 liveness).
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # -- Safety ceilings ------------------------------------------------
        {
            "name": "collect_safety",
            "description": "collect permitted only when category is anonymous OR principal is 13+ OR parental consent token is present",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"collect"',
            "resource_type": "DataPoint",
            "reference_path": os.path.join(REFS, "collect_safety.cedar"),
        },
        {
            "name": "share_safety",
            "description": "share permitted only when category is anonymous OR (behavioral/geolocation AND data subject is 13+); personal data is never shareable",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"share"',
            "resource_type": "DataPoint",
            "reference_path": os.path.join(REFS, "share_safety.cedar"),
        },
        {
            "name": "delete_safety",
            "description": "delete permitted only by the owner of the data point",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"delete"',
            "resource_type": "DataPoint",
            "reference_path": os.path.join(REFS, "delete_safety.cedar"),
        },

        # -- Floors (positive assertions) -----------------------------------
        {
            "name": "floor_collect_anonymous",
            "description": "Anonymous data collection MUST be permitted regardless of age or consent",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"collect"',
            "resource_type": "DataPoint",
            "floor_path": os.path.join(REFS, "floor_collect_anonymous.cedar"),
        },
        {
            "name": "floor_collect_13plus_personal",
            "description": "Personal data collection on 13+ users MUST be permitted (no parental consent required)",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"collect"',
            "resource_type": "DataPoint",
            "floor_path": os.path.join(REFS, "floor_collect_13plus_personal.cedar"),
        },
        {
            "name": "floor_collect_under13_with_consent",
            "description": "Personal/behavioral/geolocation collection on under-13 users with parental consent token MUST be permitted",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"collect"',
            "resource_type": "DataPoint",
            "floor_path": os.path.join(REFS, "floor_collect_under13_with_consent.cedar"),
        },
        {
            "name": "floor_share_13plus_behavioral",
            "description": "Sharing behavioral data of 13+ data subjects MUST be permitted",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"share"',
            "resource_type": "DataPoint",
            "floor_path": os.path.join(REFS, "floor_share_13plus_behavioral.cedar"),
        },
        {
            "name": "floor_delete_owner",
            "description": "Owner deleting their own data point MUST be permitted",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"delete"',
            "resource_type": "DataPoint",
            "floor_path": os.path.join(REFS, "floor_delete_owner.cedar"),
        },

        # -- Liveness -------------------------------------------------------
        {
            "name": "liveness_collect",
            "description": "User+collect+DataPoint liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"collect"',
            "resource_type": "DataPoint",
        },
        {
            "name": "liveness_share",
            "description": "User+share+DataPoint liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"share"',
            "resource_type": "DataPoint",
        },
        {
            "name": "liveness_delete",
            "description": "User+delete+DataPoint liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"delete"',
            "resource_type": "DataPoint",
        },
    ]
