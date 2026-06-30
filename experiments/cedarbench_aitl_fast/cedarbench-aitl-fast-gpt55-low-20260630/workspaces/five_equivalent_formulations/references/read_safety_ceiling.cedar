// CEILING: A User may read a Doc only when role is "admin" OR tier is 1.
// Canonical form (encoding 1). Any equivalent candidate (forms 2-5)
// must imply this ceiling.
permit (
    principal,
    action == Action::"read",
    resource
)
when {
    principal.role == "admin" || resource.tier == 1
};
