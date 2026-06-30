// Ceiling: viewHistory permitted only when:
//   (patient viewing own prescriptions) OR
//   (physician viewing prescriptions they wrote) OR
//   (nurse — any prescription for care coordination).
permit (
    principal is User,
    action == Action::"viewHistory",
    resource is Prescription
)
when {
    (principal.role == "patient" && principal == resource.patient)
    || (principal.role == "physician" && principal == resource.prescriber)
    || principal.role == "nurse"
};
