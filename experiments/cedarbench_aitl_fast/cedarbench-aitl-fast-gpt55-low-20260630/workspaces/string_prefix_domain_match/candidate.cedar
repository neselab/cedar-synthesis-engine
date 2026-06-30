permit (
    principal is User,
    action == Action::"readResource",
    resource is Resource
)
when {
    resource.classification == "public"
};

permit (
    principal is User,
    action == Action::"readResource",
    resource is Resource
)
when {
    resource.classification == "internal" &&
    principal.email like "*@example.com"
};

permit (
    principal is User,
    action == Action::"readResource",
    resource is Resource
)
when {
    resource.classification == "partner" &&
    principal.email like "*@partner.example.com"
};

permit (
    principal is User,
    action == Action::"writeResource",
    resource is Resource
)
when {
    principal.email like "admin@*"
};