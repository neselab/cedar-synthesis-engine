permit (principal is User, action == Action::"updateCourseSelection", resource is CourseSelection)
when {
    principal.role == "student"
    && context.onCampusLan
    && resource.student == principal
    && resource.isCurrentSelection
    && resource.offering.isCurrentSemester
    && resource.offering.registrationOpen
    && resource.offering.addDropOpen
};

