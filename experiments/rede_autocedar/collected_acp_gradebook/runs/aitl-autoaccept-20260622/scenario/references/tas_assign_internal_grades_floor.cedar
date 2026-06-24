permit (principal is User, action == Action::"assignInternalGrade", resource is InternalGrade) when {
    (principal.roles.contains(Role::"TeachingAssistant"))
    && !(principal.roles.contains(Role::"Student"))
};