permit (principal is User, action == Action::"viewReportCard", resource is ReportCard)
when {
    principal.role == "student"
    && context.onCampusLan
    && resource.student == principal
    && resource.previousSemesterCompleted
};

