permit (
    principal,
    action == Action::"receiveExternalGrade",
    resource
)
when {
    principal is User &&
    resource is ExternalGrade &&
    principal.roles.contains(Role::"Student")
};

permit (
    principal,
    action == Action::"receiveExternalGrade",
    resource
)
when {
    principal is User &&
    resource is ExternalGrade &&
    principal.roles.contains(Role::"FacultyFamily")
};

permit (
    principal,
    action == Action::"assignInternalGrade",
    resource
)
when {
    principal is User &&
    resource is InternalGrade &&
    principal.roles.contains(Role::"Faculty")
};

permit (
    principal,
    action == Action::"assignExternalGrade",
    resource
)
when {
    principal is User &&
    resource is ExternalGrade &&
    principal.roles.contains(Role::"Faculty")
};

permit (
    principal,
    action == Action::"viewInternalGrade",
    resource
)
when {
    principal is User &&
    resource is InternalGrade &&
    principal.roles.contains(Role::"Faculty")
};

permit (
    principal,
    action == Action::"viewExternalGrade",
    resource
)
when {
    principal is User &&
    resource is ExternalGrade &&
    principal.roles.contains(Role::"Faculty")
};

permit (
    principal,
    action == Action::"assignInternalGrade",
    resource
)
when {
    principal is User &&
    resource is InternalGrade &&
    principal.roles.contains(Role::"TeachingAssistant")
};

permit (
    principal,
    action == Action::"viewInternalGrade",
    resource
)
when {
    principal is User &&
    resource is InternalGrade &&
    principal.roles.contains(Role::"TeachingAssistant")
};

permit (
    principal,
    action == Action::"enrollInCourse",
    resource
)
when {
    principal is User &&
    resource is Course &&
    !principal.roles.contains(Role::"Faculty")
};

forbid (
    principal,
    action == Action::"assignExternalGrade",
    resource
)
when {
    principal is User &&
    resource is ExternalGrade &&
    (
        principal.roles.contains(Role::"Student") ||
        principal.roles.contains(Role::"FacultyFamily") ||
        principal.roles.contains(Role::"TeachingAssistant")
    )
};

forbid (
    principal,
    action == Action::"assignInternalGrade",
    resource
)
when {
    principal is User &&
    resource is InternalGrade &&
    principal.roles.contains(Role::"Student")
};

forbid (
    principal,
    action == Action::"viewExternalGrade",
    resource
)
when {
    principal is User &&
    resource is ExternalGrade &&
    principal.roles.contains(Role::"TeachingAssistant")
};

forbid (
    principal,
    action == Action::"enrollInCourse",
    resource
)
when {
    principal is User &&
    resource is Course &&
    principal.roles.contains(Role::"Faculty")
};