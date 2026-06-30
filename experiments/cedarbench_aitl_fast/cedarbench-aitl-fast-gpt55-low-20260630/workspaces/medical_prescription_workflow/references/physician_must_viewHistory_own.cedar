// Floor: a physician MUST be permitted to view history of prescriptions
// they wrote.
permit (
    principal is User,
    action == Action::"viewHistory",
    resource is Prescription
)
when {
    principal.role == "physician"
    && principal == resource.prescriber
};
