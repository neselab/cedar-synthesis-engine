// Floor: a User with role "user" MUST read files whose path matches
// "reports/<any chars>*-final" where the * in the middle is a LITERAL
// asterisk character in the path. The pattern uses Cedar's escape
// sequence so that `\*` matches a literal `*` (not a wildcard).
permit (
    principal is User,
    action == Action::"read",
    resource is File
)
when {
    principal.role == "user"
    && resource.path like "reports/*\*-final"
};
