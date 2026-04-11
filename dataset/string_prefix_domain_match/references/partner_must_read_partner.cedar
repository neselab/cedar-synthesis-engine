// Floor: a User whose email matches `*@partner.example.com` MUST be
// permitted to read a partner resource.
permit (
    principal is User,
    action == Action::"readResource",
    resource is Resource
)
when {
    principal.email like "*@partner.example.com"
    && resource.classification == "partner"
};
