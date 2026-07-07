permit (principal is User, action == Action::"selectTeachingOffering", resource is CourseOffering)
when {
    principal.role == "professor"
    && resource.isUpcomingSemester
    && resource.registrationOpen
    && !resource.hasTeachingConflict
    && resource.eligibleProfessors.contains(principal)
};

