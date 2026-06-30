// Floor: a physician MUST be permitted to create prescriptions.
permit (
    principal is User,
    action == Action::"create",
    resource is Prescription
)
when {
    principal.role == "physician"
};
