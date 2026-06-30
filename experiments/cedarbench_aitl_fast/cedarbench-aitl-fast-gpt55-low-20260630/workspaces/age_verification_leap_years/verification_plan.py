"""Hand-authored verification plan for realworld/age_verification_leap_years.

Age-gated content access with leap-year-correct day thresholds. Cedar's
duration constructor only accepts string literals (no expressions), so
year-to-day conversion must be hand-computed per supported minAgeYears
value (13, 18, 21) using a conservative threshold that accounts for the
maximum number of leap days in any contiguous N-year span.

Day thresholds:
  - 13 years -> 4748 days
  - 18 years -> 6575 days
  - 21 years -> 7670 days

The common failure modes this scenario hunts:
  - Candidate uses naive years*365 conversion, under-permitting near
    birthdays (or worse, under-restricting if the threshold goes the
    other way).
  - Candidate writes duration with an expression argument, which Cedar
    rejects because duration() requires a string literal.
  - Candidate forgets that Cedar duration uses Go-style "Xd" syntax
    rather than ISO 8601 "PXD".
  - Candidate uses datetime offset/comparison incorrectly (forgets to
    pin the comparison to the correct direction).
  - Candidate forgets to enumerate all three actions (view / purchase /
    subscribe), letting one leak through.
  - Candidate omits the per-resource minAgeYears guard, granting access
    to age-restricted content based on dateOfBirth alone.

10 checks total (3 ceilings + 4 floors + 3 liveness).
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # -- Safety ceilings ------------------------------------------------
        {
            "name": "view_safety",
            "description": "view permitted only when user is at least the per-resource conservative-day age old (4748d for 13+, 6575d for 18+, 7670d for 21+)",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"view"',
            "resource_type": "Content",
            "reference_path": os.path.join(REFS, "view_safety.cedar"),
        },
        {
            "name": "purchase_safety",
            "description": "purchase permitted only when user meets the same per-resource conservative-day age threshold",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"purchase"',
            "resource_type": "Content",
            "reference_path": os.path.join(REFS, "purchase_safety.cedar"),
        },
        {
            "name": "subscribe_safety",
            "description": "subscribe permitted only when user meets the same per-resource conservative-day age threshold",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"subscribe"',
            "resource_type": "Content",
            "reference_path": os.path.join(REFS, "subscribe_safety.cedar"),
        },

        # -- Floors (positive assertions) -----------------------------------
        {
            "name": "floor_view_18",
            "description": "User who is at least 6575 days old MUST be permitted to view 18+ Content",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"view"',
            "resource_type": "Content",
            "floor_path": os.path.join(REFS, "floor_view_18.cedar"),
        },
        {
            "name": "floor_purchase_21",
            "description": "User who is at least 7670 days old MUST be permitted to purchase 21+ Content",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"purchase"',
            "resource_type": "Content",
            "floor_path": os.path.join(REFS, "floor_purchase_21.cedar"),
        },
        {
            "name": "floor_view_13",
            "description": "User who is at least 4748 days old MUST be permitted to view 13+ Content",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"view"',
            "resource_type": "Content",
            "floor_path": os.path.join(REFS, "floor_view_13.cedar"),
        },
        {
            "name": "floor_subscribe_18",
            "description": "User who is at least 6575 days old MUST be permitted to subscribe to 18+ Content",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"subscribe"',
            "resource_type": "Content",
            "floor_path": os.path.join(REFS, "floor_subscribe_18.cedar"),
        },

        # -- Liveness -------------------------------------------------------
        {
            "name": "liveness_view",
            "description": "User+view+Content liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"view"',
            "resource_type": "Content",
        },
        {
            "name": "liveness_purchase",
            "description": "User+purchase+Content liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"purchase"',
            "resource_type": "Content",
        },
        {
            "name": "liveness_subscribe",
            "description": "User+subscribe+Content liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"subscribe"',
            "resource_type": "Content",
        },
    ]
