// Floor: a pharmacist MUST be permitted to fill a non-controlled,
// unfilled prescription.
permit (
    principal is User,
    action == Action::"fill",
    resource is Prescription
)
when {
    principal.role == "pharmacist"
    && !resource.isFilled
    && !resource.isControlled
};
