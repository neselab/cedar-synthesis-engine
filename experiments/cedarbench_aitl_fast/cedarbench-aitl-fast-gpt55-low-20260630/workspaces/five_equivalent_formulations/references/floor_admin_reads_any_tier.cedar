// FLOOR: An admin User MUST be permitted to read any Doc.
// Tests the admin branch of the disjunction.
permit (
    principal,
    action == Action::"read",
    resource
)
when {
    principal.role == "admin"
};
