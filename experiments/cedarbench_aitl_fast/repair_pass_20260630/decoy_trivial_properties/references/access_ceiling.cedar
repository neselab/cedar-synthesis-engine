// Ceiling: any permitted access must satisfy the rule
//   role == "admin" || (role == "user" && level <= 3)
// Candidate ⇒ this reference.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.role == "admin"
    || (principal.role == "user" && resource.level <= 3)
};
