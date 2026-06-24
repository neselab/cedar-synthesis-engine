// Policy store — verified policies appended here

// --- Verified (eval iteration 2) ---
permit (
    principal,
    action == Action::"receiveExternalGrade",
    resource
)
when {
    principal is User &&
    resource is ExternalGrade &&
    principal in Student::"Student"
};

permit (
    principal,
    action == Action::"receiveExternalGrade",
    resource
)
when {
    principal is User &&
    resource is ExternalGrade &&
    principal in FacultyFamily::"FacultyFamily"
};

forbid (
    principal,
    action == Action::"receiveExternalGrade",
    resource
)
when {
    principal is User &&
    resource is ExternalGrade &&
    principal in Faculty::"Faculty" &&
    !(principal in Student::"Student") &&
    !(principal in TeachingAssistant::"TeachingAssistant") &&
    !(principal in FacultyFamily::"FacultyFamily")
};

permit (
    principal,
    action == Action::"assignInternalGrade",
    resource
)
when {
    principal is User &&
    resource is InternalGrade &&
    principal in Faculty::"Faculty"
};

permit (
    principal,
    action == Action::"assignInternalGrade",
    resource
)
when {
    principal is User &&
    resource is InternalGrade &&
    principal in TeachingAssistant::"TeachingAssistant"
};

forbid (
    principal,
    action == Action::"assignInternalGrade",
    resource
)
when {
    principal is User &&
    resource is InternalGrade &&
    principal in Student::"Student"
};

permit (
    principal,
    action == Action::"assignExternalGrade",
    resource
)
when {
    principal is User &&
    resource is ExternalGrade &&
    principal in Faculty::"Faculty"
};

forbid (
    principal,
    action == Action::"assignExternalGrade",
    resource
)
when {
    principal is User &&
    resource is ExternalGrade &&
    principal in Student::"Student"
};

forbid (
    principal,
    action == Action::"assignExternalGrade",
    resource
)
when {
    principal is User &&
    resource is ExternalGrade &&
    principal in TeachingAssistant::"TeachingAssistant"
};

forbid (
    principal,
    action == Action::"assignExternalGrade",
    resource
)
when {
    principal is User &&
    resource is ExternalGrade &&
    principal in FacultyFamily::"FacultyFamily"
};

permit (
    principal,
    action == Action::"viewInternalGrade",
    resource
)
when {
    principal is User &&
    resource is InternalGrade &&
    principal in Faculty::"Faculty"
};

permit (
    principal,
    action == Action::"viewInternalGrade",
    resource
)
when {
    principal is User &&
    resource is InternalGrade &&
    principal in TeachingAssistant::"TeachingAssistant"
};

permit (
    principal,
    action == Action::"viewExternalGrade",
    resource
)
when {
    principal is User &&
    resource is ExternalGrade &&
    principal in Faculty::"Faculty"
};

forbid (
    principal,
    action == Action::"viewExternalGrade",
    resource
)
when {
    principal is User &&
    resource is ExternalGrade &&
    principal in TeachingAssistant::"TeachingAssistant"
};

permit (
    principal,
    action == Action::"enrollInCourse",
    resource
)
when {
    principal is User &&
    resource is Course &&
    !(principal in Faculty::"Faculty")
};
