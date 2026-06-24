permit (principal, action == Action::"assignInternalGrade", resource) when {
    (principal in Faculty::"Faculty" && resource is InternalGrade)
    && !(principal in Student::"Student")
};