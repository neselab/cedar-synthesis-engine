// Floor: controller MUST delete any record.
permit (
    principal is User,
    action == Action::"delete",
    resource is DataRecord
)
when {
    principal.role == "controller"
};
