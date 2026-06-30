"""Hand-authored verification plan for realworld/educational_gradebook.

Teacher/student/parent visibility rules for academic grades. Tests:
  - Role-based access (teacher, student, parent) on same resource type
  - Optional context attribute (parentOf?: User) with has-guarding
  - Boolean attribute gating (isFinal blocks editGrade)
  - Self-access pattern (principal == resource.studentId)
  - Class-scoped visibility (assignedClass must match)

Hunts for failure modes:
  - Missing `has` guard on optional `context.parentOf` (§8.3 trap)
  - Allowing parents to edit or publish grades
  - Forgetting isFinal guard on editGrade
  - Allowing cross-class teacher access
  - Collapsing student self-view into class-scoped view (losing the
    principal == resource.studentId constraint)
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # -- Safety ceilings ------------------------------------------------
        {
            "name": "viewGrade_safety",
            "description": "viewGrade permitted only when teacher in same class, OR student self-access, OR parent with valid parentOf",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"viewGrade"',
            "resource_type": "GradeRecord",
            "reference_path": os.path.join(REFS, "viewGrade_safety.cedar"),
        },
        {
            "name": "editGrade_safety",
            "description": "editGrade permitted only when teacher in same class AND grade is not final",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"editGrade"',
            "resource_type": "GradeRecord",
            "reference_path": os.path.join(REFS, "editGrade_safety.cedar"),
        },
        {
            "name": "publishGrade_safety",
            "description": "publishGrade permitted only when teacher in same class",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"publishGrade"',
            "resource_type": "GradeRecord",
            "reference_path": os.path.join(REFS, "publishGrade_safety.cedar"),
        },
        {
            "name": "viewClassAverage_safety",
            "description": "viewClassAverage permitted only when teacher or student in same class",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"viewClassAverage"',
            "resource_type": "GradeRecord",
            "reference_path": os.path.join(REFS, "viewClassAverage_safety.cedar"),
        },

        # -- Floors ---------------------------------------------------------
        {
            "name": "teacher_view_grade",
            "description": "Teacher in same class MUST be permitted to viewGrade",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"viewGrade"',
            "resource_type": "GradeRecord",
            "floor_path": os.path.join(REFS, "teacher_view_grade.cedar"),
        },
        {
            "name": "student_self_view_grade",
            "description": "Student MUST be permitted to viewGrade on their own grade",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"viewGrade"',
            "resource_type": "GradeRecord",
            "floor_path": os.path.join(REFS, "student_self_view_grade.cedar"),
        },
        {
            "name": "parent_view_grade",
            "description": "Parent with valid parentOf MUST be permitted to viewGrade on their child's grade",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"viewGrade"',
            "resource_type": "GradeRecord",
            "floor_path": os.path.join(REFS, "parent_view_grade.cedar"),
        },
        {
            "name": "teacher_edit_nonfinal",
            "description": "Teacher in same class MUST be permitted to editGrade when grade is not final",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"editGrade"',
            "resource_type": "GradeRecord",
            "floor_path": os.path.join(REFS, "teacher_edit_nonfinal.cedar"),
        },
        {
            "name": "teacher_publish",
            "description": "Teacher in same class MUST be permitted to publishGrade",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"publishGrade"',
            "resource_type": "GradeRecord",
            "floor_path": os.path.join(REFS, "teacher_publish.cedar"),
        },
        {
            "name": "teacher_view_avg",
            "description": "Teacher in same class MUST be permitted to viewClassAverage",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"viewClassAverage"',
            "resource_type": "GradeRecord",
            "floor_path": os.path.join(REFS, "teacher_view_avg.cedar"),
        },
        {
            "name": "student_view_avg",
            "description": "Student in same class MUST be permitted to viewClassAverage",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"viewClassAverage"',
            "resource_type": "GradeRecord",
            "floor_path": os.path.join(REFS, "student_view_avg.cedar"),
        },

        # -- Liveness -------------------------------------------------------
        {
            "name": "liveness_viewGrade",
            "description": "User+viewGrade+GradeRecord liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"viewGrade"',
            "resource_type": "GradeRecord",
        },
        {
            "name": "liveness_editGrade",
            "description": "User+editGrade+GradeRecord liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"editGrade"',
            "resource_type": "GradeRecord",
        },
        {
            "name": "liveness_publishGrade",
            "description": "User+publishGrade+GradeRecord liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"publishGrade"',
            "resource_type": "GradeRecord",
        },
        {
            "name": "liveness_viewClassAverage",
            "description": "User+viewClassAverage+GradeRecord liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"viewClassAverage"',
            "resource_type": "GradeRecord",
        },
    ]
