"""Hand-authored verification plan for realworld/ferpa_age_18_transition.

Encodes FERPA's age-of-majority transition: parental rights to a
student's educational record (inspect, request correction) transfer to
the student on the 18th birthday. School officials retain access at
all ages under the legitimate-educational-interest exception.

Day-threshold convention (matches age_verification_leap_years):
  18 years -> 6575 days (= 18*365 + 5 worst-case leap days).
A student is "at least 18" when
  context.now.durationSince(studentId.dateOfBirth) >= duration("6575d").

Common failure modes this scenario hunts:
  - Candidate uses the *principal's* dateOfBirth instead of the
    *student's* (resource.studentId.dateOfBirth) when computing whether
    rights have transferred. The age that matters is the student's, not
    the parent's.
  - Candidate writes the parent revocation as a `forbid when ... >= 6575d`,
    which over-blocks a person who happens to be both a parent AND a
    school_official (CLAUDE.md §8.6 role-intersection trap). Correct
    encoding is positive permits gated by `< 6575d`.
  - Candidate forgets `principal == resource.studentId` on the "self"
    branch, allowing any user with relationshipToStudent == "self" to
    read someone else's record.
  - Candidate forgets that disclose is school_official-only and
    incidentally permits parent / guardian / self to disclose.
  - Candidate uses `>` instead of `>=` (or `<=` instead of `<`) at the
    age threshold, mishandling the exact-18 boundary.
  - Candidate uses ISO 8601 duration syntax (CLAUDE.md §8.9).
  - Candidate uses naive `years * 365` and lets a 17-year-and-360-day
    student's parent be denied (or vice versa) near a leap-year
    boundary.

11 checks total: 3 ceilings + 5 floors + 3 liveness.
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # -- Safety ceilings ------------------------------------------------
        {
            "name": "view_safety",
            "description": "viewRecord permitted only for: the student themselves (==studentId & 'self'), parent/guardian when student is under 18 (<6575d), or school_official",
            "type": "implies",
            "principal_type": "Person",
            "action": 'Action::"viewRecord"',
            "resource_type": "EducationalRecord",
            "reference_path": os.path.join(REFS, "view_safety.cedar"),
        },
        {
            "name": "correction_safety",
            "description": "requestCorrection mirrors viewRecord access exactly (paired FERPA rights)",
            "type": "implies",
            "principal_type": "Person",
            "action": 'Action::"requestCorrection"',
            "resource_type": "EducationalRecord",
            "reference_path": os.path.join(REFS, "correction_safety.cedar"),
        },
        {
            "name": "disclose_safety",
            "description": "disclose (third-party release) restricted to school_official only",
            "type": "implies",
            "principal_type": "Person",
            "action": 'Action::"disclose"',
            "resource_type": "EducationalRecord",
            "reference_path": os.path.join(REFS, "disclose_safety.cedar"),
        },

        # -- Floors (positive assertions) -----------------------------------
        {
            "name": "floor_school_official_view",
            "description": "school_official MUST be permitted to viewRecord on any EducationalRecord regardless of student age",
            "type": "floor",
            "principal_type": "Person",
            "action": 'Action::"viewRecord"',
            "resource_type": "EducationalRecord",
            "floor_path": os.path.join(REFS, "floor_school_official_view.cedar"),
        },
        {
            "name": "floor_school_official_correct",
            "description": "school_official MUST be permitted to requestCorrection on any EducationalRecord regardless of student age",
            "type": "floor",
            "principal_type": "Person",
            "action": 'Action::"requestCorrection"',
            "resource_type": "EducationalRecord",
            "floor_path": os.path.join(REFS, "floor_school_official_correct.cedar"),
        },
        {
            "name": "floor_school_official_disclose",
            "description": "school_official MUST be permitted to disclose any EducationalRecord",
            "type": "floor",
            "principal_type": "Person",
            "action": 'Action::"disclose"',
            "resource_type": "EducationalRecord",
            "floor_path": os.path.join(REFS, "floor_school_official_disclose.cedar"),
        },
        {
            "name": "floor_parent_minor_view",
            "description": "parent MUST be permitted to viewRecord when the student is strictly under 18 (<6575d since DOB)",
            "type": "floor",
            "principal_type": "Person",
            "action": 'Action::"viewRecord"',
            "resource_type": "EducationalRecord",
            "floor_path": os.path.join(REFS, "floor_parent_minor_view.cedar"),
        },
        {
            "name": "floor_self_view",
            "description": "student themselves (principal == studentId AND relationshipToStudent == 'self') MUST be permitted to viewRecord",
            "type": "floor",
            "principal_type": "Person",
            "action": 'Action::"viewRecord"',
            "resource_type": "EducationalRecord",
            "floor_path": os.path.join(REFS, "floor_self_view.cedar"),
        },

        # -- Liveness -------------------------------------------------------
        {
            "name": "liveness_view",
            "description": "Person+viewRecord+EducationalRecord liveness",
            "type": "always-denies-liveness",
            "principal_type": "Person",
            "action": 'Action::"viewRecord"',
            "resource_type": "EducationalRecord",
        },
        {
            "name": "liveness_correction",
            "description": "Person+requestCorrection+EducationalRecord liveness",
            "type": "always-denies-liveness",
            "principal_type": "Person",
            "action": 'Action::"requestCorrection"',
            "resource_type": "EducationalRecord",
        },
        {
            "name": "liveness_disclose",
            "description": "Person+disclose+EducationalRecord liveness",
            "type": "always-denies-liveness",
            "principal_type": "Person",
            "action": 'Action::"disclose"',
            "resource_type": "EducationalRecord",
        },
    ]
