// Floor: a pharmacist MUST be permitted to review any prescription.
permit (
    principal is User,
    action == Action::"review",
    resource is Prescription
)
when {
    principal.role == "pharmacist"
};
