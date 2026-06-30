// Floor: a Worker with role "manager" MUST be permitted to edit any
// Record. (Managers retain edit power on top of delete power.)
permit (
    principal is Worker,
    action == Action::"edit",
    resource is Record
)
when {
    principal.role == "manager"
};
