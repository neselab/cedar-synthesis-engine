#!/usr/bin/env python3
"""Hidden verifier for the course-registration Cedar synthesis task.

The tests use Cedar validation plus symbolic containment checks. They accept
any policy denotation that satisfies the hidden floor, ceiling, and liveness
properties; they do not require the oracle policy's syntax or structure.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import os
from pathlib import Path


APP = Path(os.environ.get("APP_DIR", "/app"))
SCHEMA = APP / "schema.cedarschema"
POLICY = APP / "policy.cedar"


CHECKS = [
    {
        "name": "browse_catalogue_only_students_on_lan",
        "type": "ceiling",
        "principal_type": "User",
        "action": 'Action::"browseCatalogue"',
        "resource_type": "CourseOffering",
        "reference": """
permit (principal is User, action == Action::"browseCatalogue", resource is CourseOffering)
when { principal.role == "student" && context.fromCampusLAN };
""",
    },
    {
        "name": "student_browse_catalogue_on_lan_floor",
        "type": "floor",
        "principal_type": "User",
        "action": 'Action::"browseCatalogue"',
        "resource_type": "CourseOffering",
        "reference": """
permit (principal is User, action == Action::"browseCatalogue", resource is CourseOffering)
when { principal.role == "student" && context.fromCampusLAN };
""",
    },
    {
        "name": "add_course_only_own_open_selection",
        "type": "ceiling",
        "principal_type": "User",
        "action": 'Action::"addCourse"',
        "resource_type": "CourseSelection",
        "reference": """
permit (principal is User, action == Action::"addCourse", resource is CourseSelection)
when { principal.role == "student" && principal == resource.student && resource.registrationOpen };
""",
    },
    {
        "name": "drop_course_only_own_open_selection",
        "type": "ceiling",
        "principal_type": "User",
        "action": 'Action::"dropCourse"',
        "resource_type": "CourseSelection",
        "reference": """
permit (principal is User, action == Action::"dropCourse", resource is CourseSelection)
when { principal.role == "student" && principal == resource.student && resource.registrationOpen };
""",
    },
    {
        "name": "update_course_only_own_open_selection",
        "type": "ceiling",
        "principal_type": "User",
        "action": 'Action::"updateCourseSelection"',
        "resource_type": "CourseSelection",
        "reference": """
permit (principal is User, action == Action::"updateCourseSelection", resource is CourseSelection)
when { principal.role == "student" && principal == resource.student && resource.registrationOpen };
""",
    },
    {
        "name": "student_add_open_own_selection_floor",
        "type": "floor",
        "principal_type": "User",
        "action": 'Action::"addCourse"',
        "resource_type": "CourseSelection",
        "reference": """
permit (principal is User, action == Action::"addCourse", resource is CourseSelection)
when { principal.role == "student" && principal == resource.student && resource.registrationOpen };
""",
    },
    {
        "name": "view_report_card_only_self_completed",
        "type": "ceiling",
        "principal_type": "User",
        "action": 'Action::"viewReportCard"',
        "resource_type": "ReportCard",
        "reference": """
permit (principal is User, action == Action::"viewReportCard", resource is ReportCard)
when { principal.role == "student" && principal == resource.student && resource.semesterCompleted };
""",
    },
    {
        "name": "student_view_own_completed_report_card_floor",
        "type": "floor",
        "principal_type": "User",
        "action": 'Action::"viewReportCard"',
        "resource_type": "ReportCard",
        "reference": """
permit (principal is User, action == Action::"viewReportCard", resource is ReportCard)
when { principal.role == "student" && principal == resource.student && resource.semesterCompleted };
""",
    },
    {
        "name": "professor_select_only_eligible_no_conflict_open",
        "type": "ceiling",
        "principal_type": "User",
        "action": 'Action::"selectTeachingOffering"',
        "resource_type": "CourseOffering",
        "reference": """
permit (principal is User, action == Action::"selectTeachingOffering", resource is CourseOffering)
when {
    principal.role == "professor"
    && resource.registrationOpen
    && !resource.hasScheduleConflict
    && resource.eligibleProfessors.contains(principal)
};
""",
    },
    {
        "name": "eligible_professor_select_open_no_conflict_floor",
        "type": "floor",
        "principal_type": "User",
        "action": 'Action::"selectTeachingOffering"',
        "resource_type": "CourseOffering",
        "reference": """
permit (principal is User, action == Action::"selectTeachingOffering", resource is CourseOffering)
when {
    principal.role == "professor"
    && resource.registrationOpen
    && !resource.hasScheduleConflict
    && resource.eligibleProfessors.contains(principal)
};
""",
    },
    {
        "name": "professor_view_only_own_roster",
        "type": "ceiling",
        "principal_type": "User",
        "action": 'Action::"viewRoster"',
        "resource_type": "Roster",
        "reference": """
permit (principal is User, action == Action::"viewRoster", resource is Roster)
when { principal.role == "professor" && principal == resource.instructor };
""",
    },
    {
        "name": "professor_enter_grades_only_own_completed_class",
        "type": "ceiling",
        "principal_type": "User",
        "action": 'Action::"enterGrade"',
        "resource_type": "GradeEntry",
        "reference": """
permit (principal is User, action == Action::"enterGrade", resource is GradeEntry)
when { principal.role == "professor" && principal == resource.instructor && resource.semesterCompleted };
""",
    },
    {
        "name": "professor_enter_own_completed_grade_floor",
        "type": "floor",
        "principal_type": "User",
        "action": 'Action::"enterGrade"',
        "resource_type": "GradeEntry",
        "reference": """
permit (principal is User, action == Action::"enterGrade", resource is GradeEntry)
when { principal.role == "professor" && principal == resource.instructor && resource.semesterCompleted };
""",
    },
    {
        "name": "only_registrar_changes_student_information",
        "type": "ceiling",
        "principal_type": "User",
        "action": 'Action::"changeStudentInformation"',
        "resource_type": "StudentInformation",
        "reference": """
permit (principal is User, action == Action::"changeStudentInformation", resource is StudentInformation)
when { principal.role == "registrar" };
""",
    },
    {
        "name": "only_registrar_closes_registration",
        "type": "ceiling",
        "principal_type": "User",
        "action": 'Action::"closeRegistration"',
        "resource_type": "RegistrationProcess",
        "reference": """
permit (principal is User, action == Action::"closeRegistration", resource is RegistrationProcess)
when { principal.role == "registrar" };
""",
    },
    {
        "name": "registrar_close_registration_floor",
        "type": "floor",
        "principal_type": "User",
        "action": 'Action::"closeRegistration"',
        "resource_type": "RegistrationProcess",
        "reference": """
permit (principal is User, action == Action::"closeRegistration", resource is RegistrationProcess)
when { principal.role == "registrar" };
""",
    },
]


LIVENESS = [
    ("liveness_add_course", "User", 'Action::"addCourse"', "CourseSelection"),
    ("liveness_view_report_card", "User", 'Action::"viewReportCard"', "ReportCard"),
    ("liveness_select_teaching", "User", 'Action::"selectTeachingOffering"', "CourseOffering"),
    ("liveness_enter_grade", "User", 'Action::"enterGrade"', "GradeEntry"),
    ("liveness_close_registration", "User", 'Action::"closeRegistration"', "RegistrationProcess"),
]


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)


def cedar_base(principal_type: str, action: str, resource_type: str) -> list[str]:
    return [
        "cedar",
        "symcc",
        "--schema",
        str(SCHEMA),
        "--principal-type",
        principal_type,
        "--action",
        action,
        "--resource-type",
        resource_type,
    ]


def check_verified(result: subprocess.CompletedProcess[str], name: str) -> bool:
    output = result.stdout
    ok = result.returncode == 0 and "VERIFIED" in output and "COUNTEREXAMPLE" not in output
    if not ok:
        print(f"\n[FAIL] {name}\n{output}", file=sys.stderr)
    return ok


def main() -> int:
    if not POLICY.exists():
        print("/app/policy.cedar does not exist", file=sys.stderr)
        return 1

    validation = run(["cedar", "validate", "--schema", str(SCHEMA), "--policies", str(POLICY)])
    if validation.returncode != 0:
        print("[FAIL] cedar validate failed", file=sys.stderr)
        print(validation.stdout, file=sys.stderr)
        return 1

    with tempfile.TemporaryDirectory() as td:
        temp = Path(td)
        ok = True
        for check in CHECKS:
            ref = temp / f"{check['name']}.cedar"
            ref.write_text(check["reference"].strip() + "\n")
            ref_validation = run(["cedar", "validate", "--schema", str(SCHEMA), "--policies", str(ref)])
            if ref_validation.returncode != 0:
                print(f"[INTERNAL ERROR] reference failed validation: {check['name']}", file=sys.stderr)
                print(ref_validation.stdout, file=sys.stderr)
                return 1

            if check["type"] == "ceiling":
                cmd = cedar_base(check["principal_type"], check["action"], check["resource_type"]) + [
                    "implies",
                    "--policies1",
                    str(POLICY),
                    "--policies2",
                    str(ref),
                ]
            elif check["type"] == "floor":
                cmd = cedar_base(check["principal_type"], check["action"], check["resource_type"]) + [
                    "implies",
                    "--policies1",
                    str(ref),
                    "--policies2",
                    str(POLICY),
                ]
            else:
                raise AssertionError(check)
            ok = check_verified(run(cmd), check["name"]) and ok

        for name, principal_type, action, resource_type in LIVENESS:
            # Liveness passes iff the candidate is NOT proved to always deny.
            result = run(cedar_base(principal_type, action, resource_type) + ["always-denies", "--policies", str(POLICY)])
            live = result.returncode != 0 or "VERIFIED" not in result.stdout
            if not live:
                print(f"\n[FAIL] {name}: policy always denies this request class", file=sys.stderr)
                print(result.stdout, file=sys.stderr)
            ok = live and ok

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
