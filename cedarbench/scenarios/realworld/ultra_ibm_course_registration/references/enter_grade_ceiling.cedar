permit (principal is User, action == Action::"enterGrade", resource is GradeRecord)
when {
    principal.role == "professor"
    && resource.previousSemesterCompleted
    && resource.professor == principal
    && resource.offering has instructor
    && resource.offering.instructor == principal
};

