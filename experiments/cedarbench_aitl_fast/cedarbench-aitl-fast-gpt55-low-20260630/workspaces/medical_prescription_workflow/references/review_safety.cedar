// Ceiling: review permitted only when:
//   (pharmacist) OR
//   (physician who wrote the prescription) OR
//   (patient the prescription is for).
permit (
    principal is User,
    action == Action::"review",
    resource is Prescription
)
when {
    principal.role == "pharmacist"
    || (principal.role == "physician" && principal == resource.prescriber)
    || (principal.role == "patient" && principal == resource.patient)
};
