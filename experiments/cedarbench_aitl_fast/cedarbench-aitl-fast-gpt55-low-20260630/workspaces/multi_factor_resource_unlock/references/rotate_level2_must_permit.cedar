// Floor: a security_officer with hasMfa MUST be able to rotate a
// level-2 secret (levels 1 and 2 share the same factor requirement
// for rotate, so level 2 is representative).
permit (
    principal is User,
    action == Action::"rotate",
    resource is Secret
)
when {
    principal.role == "security_officer"
    && context.hasMfa
    && resource.sensitivityLevel == 2
};
