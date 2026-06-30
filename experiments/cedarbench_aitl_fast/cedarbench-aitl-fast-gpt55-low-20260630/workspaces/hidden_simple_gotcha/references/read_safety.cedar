// Ceiling: read may only be permitted when principal is current owner
// OR original creator. Anyone else reading the file is a safety violation.
permit (
    principal is User,
    action == Action::"read",
    resource is File
)
when {
    principal == resource.currentOwner ||
    principal == resource.creator
};
