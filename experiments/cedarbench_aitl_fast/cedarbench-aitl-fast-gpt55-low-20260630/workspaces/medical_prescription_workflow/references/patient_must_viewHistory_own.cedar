// Floor: a patient MUST be permitted to view history of their own prescriptions.
permit (
    principal is User,
    action == Action::"viewHistory",
    resource is Prescription
)
when {
    principal.role == "patient"
    && principal == resource.patient
};
