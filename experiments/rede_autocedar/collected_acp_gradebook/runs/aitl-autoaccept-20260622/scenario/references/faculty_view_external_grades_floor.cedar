permit (principal is User, action == Action::"viewExternalGrade", resource is ExternalGrade) when {
    (principal.roles.contains(Role::"Faculty"))
    && !(principal.roles.contains(Role::"TeachingAssistant"))
};