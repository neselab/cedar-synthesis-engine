// Floor: a user MUST be permitted to delete data points they own.
// This satisfies COPPA §312.6 (parent's right to review and delete
// at the host application's pre-validated request) as well as
// general data-subject-driven deletion rights.
permit (
    principal is User,
    action == Action::"delete",
    resource is DataPoint
)
when {
    principal == resource.owner
};
