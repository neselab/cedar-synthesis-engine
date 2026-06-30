// Ceiling: create permitted only when role == "physician".
permit (
    principal is User,
    action == Action::"create",
    resource is Prescription
)
when {
    principal.role == "physician"
};
