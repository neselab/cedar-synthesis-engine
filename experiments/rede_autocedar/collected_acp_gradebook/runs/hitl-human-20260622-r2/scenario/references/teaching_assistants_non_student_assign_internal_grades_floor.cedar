permit (principal, action == Action::"assignInternalGrade", resource) when {
    (principal in TeachingAssistant::"TeachingAssistant" && !(principal in Student::"Student") && resource is InternalGrade)
    && !(principal in Student::"Student")
};