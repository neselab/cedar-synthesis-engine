// Ceiling: writeResource permitted only for users whose email starts
// with "admin@" (matched via Cedar's `like` glob operator).
permit (
    principal is User,
    action == Action::"writeResource",
    resource is Resource
)
when {
    principal.email like "admin@*"
};
