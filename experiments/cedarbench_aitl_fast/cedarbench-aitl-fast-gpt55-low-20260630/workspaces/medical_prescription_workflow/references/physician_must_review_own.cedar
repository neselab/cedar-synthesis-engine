// Floor: a physician MUST be permitted to review prescriptions they wrote.
permit (
    principal is User,
    action == Action::"review",
    resource is Prescription
)
when {
    principal.role == "physician"
    && principal == resource.prescriber
};
