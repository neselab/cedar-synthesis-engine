permit (principal, action == Action::"receiveExternalGrade", resource) when {
    (principal in Student::"Student" && resource is ExternalGrade)
    && !(principal in Faculty::"Faculty" && !(principal in Student::"Student") && !(principal in TeachingAssistant::"TeachingAssistant") && !(principal in FacultyFamily::"FacultyFamily"))
};