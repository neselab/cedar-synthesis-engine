// Floor: a pharmacist MUST be permitted to fill a controlled-substance
// prescription that is unfilled, when context attests verification.
permit (
    principal is User,
    action == Action::"fill",
    resource is Prescription
)
when {
    principal.role == "pharmacist"
    && !resource.isFilled
    && resource.isControlled
    && context has controlledSubstanceVerified
    && context.controlledSubstanceVerified
};
