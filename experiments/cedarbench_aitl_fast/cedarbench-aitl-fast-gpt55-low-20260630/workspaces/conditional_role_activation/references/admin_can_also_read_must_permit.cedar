// Floor: an Employee with admin homeRole MUST also be permitted to read
// a SecureSystem (read access is universal — admins are not excluded).
permit (
    principal is Employee,
    action == Action::"read",
    resource is SecureSystem
)
when {
    principal.homeRole == "admin"
};
