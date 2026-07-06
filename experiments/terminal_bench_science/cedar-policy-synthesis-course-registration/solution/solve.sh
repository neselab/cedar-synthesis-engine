#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/app}"

cat > "$APP_DIR/policy.cedar" <<'CEDAR'
permit (
    principal is User,
    action == Action::"browseCatalogue",
    resource is CourseOffering
)
when {
    principal.role == "student"
    && context.fromCampusLAN
};

permit (
    principal is User,
    action in [
        Action::"addCourse",
        Action::"dropCourse",
        Action::"updateCourseSelection"
    ],
    resource is CourseSelection
)
when {
    principal.role == "student"
    && principal == resource.student
    && resource.registrationOpen
};

permit (
    principal is User,
    action == Action::"viewReportCard",
    resource is ReportCard
)
when {
    principal.role == "student"
    && principal == resource.student
    && resource.semesterCompleted
};

permit (
    principal is User,
    action == Action::"selectTeachingOffering",
    resource is CourseOffering
)
when {
    principal.role == "professor"
    && resource.registrationOpen
    && !resource.hasScheduleConflict
    && resource.eligibleProfessors.contains(principal)
};

permit (
    principal is User,
    action == Action::"viewRoster",
    resource is Roster
)
when {
    principal.role == "professor"
    && principal == resource.instructor
};

permit (
    principal is User,
    action == Action::"enterGrade",
    resource is GradeEntry
)
when {
    principal.role == "professor"
    && principal == resource.instructor
    && resource.semesterCompleted
};

permit (
    principal is User,
    action == Action::"changeStudentInformation",
    resource is StudentInformation
)
when {
    principal.role == "registrar"
};

permit (
    principal is User,
    action == Action::"closeRegistration",
    resource is RegistrationProcess
)
when {
    principal.role == "registrar"
};
CEDAR

cedar validate --schema "$APP_DIR/schema.cedarschema" --policies "$APP_DIR/policy.cedar"
