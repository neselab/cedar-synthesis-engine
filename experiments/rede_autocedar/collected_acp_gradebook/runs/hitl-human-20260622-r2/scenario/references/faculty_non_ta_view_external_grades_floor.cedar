permit (principal, action == Action::"viewExternalGrade", resource) when {
    (principal in Faculty::"Faculty" && !(principal in TeachingAssistant::"TeachingAssistant") && resource is ExternalGrade)
    && !(principal in TeachingAssistant::"TeachingAssistant")
};