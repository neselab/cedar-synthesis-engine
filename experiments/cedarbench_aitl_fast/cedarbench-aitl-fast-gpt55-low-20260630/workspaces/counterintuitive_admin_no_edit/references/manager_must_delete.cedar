// Floor: a Worker with role "manager" MUST be permitted to delete any
// Record. (Managers are the only role with delete power.)
permit (
    principal is Worker,
    action == Action::"delete",
    resource is Record
)
when {
    principal.role == "manager"
};
