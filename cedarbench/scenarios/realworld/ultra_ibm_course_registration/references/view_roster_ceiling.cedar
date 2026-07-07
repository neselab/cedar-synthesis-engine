permit (principal is User, action == Action::"viewRoster", resource is CourseOffering)
when {
    principal.role == "professor"
    && resource has instructor
    && resource.instructor == principal
};

