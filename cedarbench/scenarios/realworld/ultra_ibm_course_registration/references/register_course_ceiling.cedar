permit (principal is User, action == Action::"registerCourse", resource is CourseSelection)
when {
    principal.role == "student"
    && context.onCampusLan
    && resource.student == principal
    && resource.offering.isCurrentSemester
    && resource.offering.registrationOpen
};

