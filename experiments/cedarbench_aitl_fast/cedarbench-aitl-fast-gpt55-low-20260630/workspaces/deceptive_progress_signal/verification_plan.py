"""Hand-authored verification plan for realworld/deceptive_progress_signal.

Adversarial 3x3 (role x action) matrix where each cell has subtly
different subject-scope or exclusion rules. Designed to construct
fix-A-break-B oscillations that defeat:
  - §8.2 hash-based oscillation detection (each candidate is genuinely
    different — the hash never repeats),
  - set-based progress detection (violation count plausibly decreases
    monotonically across several wrong steps),

and that can ONLY be navigated correctly by:
  - §8.1 directional per-violation feedback (each violated floor /
    ceiling needs its own specific fix),
  - §8.6 role-intersection awareness (don't `forbid when role == "ta"`
    on editGrade — it breaks the instructor-bypass floor when a TA is
    the listed instructor).

Hunts for failure modes:
  - Synthesizer "unifies" teacher rules across all three actions
    (giving teachers an unscoped permit on editGrade or addComment),
  - Synthesizer adds an unscoped TA permit on viewGrade (matching the
    unscoped teacher permit by symmetry),
  - Synthesizer adds `forbid when role == "ta"` on editGrade
    (breaking the instructor-bypass floor),
  - Synthesizer collapses viewGrade and addComment TA rules into one
    permit then drops the subject scope,
  - Synthesizer copies the editGrade subject-scoped teacher permit
    into viewGrade (under-permitting teachers in other depts).
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # -- Safety ceilings (3) --------------------------------------------
        {
            "name": "viewGrade_safety",
            "description": "viewGrade permitted only when teacher (any dept) OR TA in same subject OR student viewing own exam",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"viewGrade"',
            "resource_type": "Exam",
            "reference_path": os.path.join(REFS, "viewGrade_safety.cedar"),
        },
        {
            "name": "editGrade_safety",
            "description": "editGrade permitted only when teacher in same subject OR principal is the listed instructor",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"editGrade"',
            "resource_type": "Exam",
            "reference_path": os.path.join(REFS, "editGrade_safety.cedar"),
        },
        {
            "name": "addComment_safety",
            "description": "addComment permitted only when teacher OR TA in same subject; never students",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"addComment"',
            "resource_type": "Exam",
            "reference_path": os.path.join(REFS, "addComment_safety.cedar"),
        },

        # -- Floors (6) -----------------------------------------------------
        {
            "name": "teacher_view_any",
            "description": "Any teacher (any dept) MUST be permitted to viewGrade — viewGrade is unscoped for teachers",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"viewGrade"',
            "resource_type": "Exam",
            "floor_path": os.path.join(REFS, "teacher_view_any.cedar"),
        },
        {
            "name": "ta_view_own_subject",
            "description": "TA in matching subject MUST be permitted to viewGrade",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"viewGrade"',
            "resource_type": "Exam",
            "floor_path": os.path.join(REFS, "ta_view_own_subject.cedar"),
        },
        {
            "name": "student_view_self",
            "description": "Student MUST be permitted to viewGrade on their own exam (principal == resource.student)",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"viewGrade"',
            "resource_type": "Exam",
            "floor_path": os.path.join(REFS, "student_view_self.cedar"),
        },
        {
            "name": "teacher_edit_subject",
            "description": "Teacher in matching subject MUST be permitted to editGrade",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"editGrade"',
            "resource_type": "Exam",
            "floor_path": os.path.join(REFS, "teacher_edit_subject.cedar"),
        },
        {
            "name": "instructor_edit_any",
            "description": "Listed instructor MUST be permitted to editGrade regardless of role (§8.6 trap: don't blanket-forbid TAs)",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"editGrade"',
            "resource_type": "Exam",
            "floor_path": os.path.join(REFS, "instructor_edit_any.cedar"),
        },
        {
            "name": "ta_comment_subject",
            "description": "TA in matching subject MUST be permitted to addComment (parallel to ta_view_own_subject — but editGrade has NO TA path)",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"addComment"',
            "resource_type": "Exam",
            "floor_path": os.path.join(REFS, "ta_comment_subject.cedar"),
        },

        # -- Liveness (3) ---------------------------------------------------
        {
            "name": "liveness_viewGrade",
            "description": "User+viewGrade+Exam liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"viewGrade"',
            "resource_type": "Exam",
        },
        {
            "name": "liveness_editGrade",
            "description": "User+editGrade+Exam liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"editGrade"',
            "resource_type": "Exam",
        },
        {
            "name": "liveness_addComment",
            "description": "User+addComment+Exam liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"addComment"',
            "resource_type": "Exam",
        },
    ]
