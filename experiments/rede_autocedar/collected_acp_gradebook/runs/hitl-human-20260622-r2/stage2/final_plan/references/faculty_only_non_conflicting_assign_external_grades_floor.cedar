permit (principal, action == Action::"assignExternalGrade", resource) when {
    (principal in Faculty::"Faculty" && !(principal in Student::"Student") && !(principal in TeachingAssistant::"TeachingAssistant") && !(principal in FacultyFamily::"FacultyFamily") && resource is ExternalGrade)
    && !(principal in Student::"Student")
    && !(principal in TeachingAssistant::"TeachingAssistant")
    && !(principal in FacultyFamily::"FacultyFamily")
};