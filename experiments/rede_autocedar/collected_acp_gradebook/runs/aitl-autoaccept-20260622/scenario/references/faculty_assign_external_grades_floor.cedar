permit (principal is User, action == Action::"assignExternalGrade", resource is ExternalGrade) when {
    (principal.roles.contains(Role::"Faculty") && !principal.roles.contains(Role::"Student") && !principal.roles.contains(Role::"FacultyFamily"))
    && !(principal.roles.contains(Role::"Student"))
    && !(principal.roles.contains(Role::"Student") || principal.roles.contains(Role::"FacultyFamily"))
    && !(principal.roles.contains(Role::"TeachingAssistant"))
};