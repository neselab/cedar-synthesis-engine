// Floor: a patient MUST be permitted to review their own prescriptions.
permit (
    principal is User,
    action == Action::"review",
    resource is Prescription
)
when {
    principal.role == "patient"
    && principal == resource.patient
};
