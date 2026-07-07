permit (principal is User, action == Action::"modifyAssignedOffering", resource is CourseOffering)
when {
    principal.role == "professor"
    && resource.registrationOpen
    && resource has instructor
    && resource.instructor == principal
};

