// Ceiling: fill permitted only when:
//   role == "pharmacist" AND
//   prescription not already filled AND
//   (not controlled OR (context has controlledSubstanceVerified AND it is true)).
permit (
    principal is User,
    action == Action::"fill",
    resource is Prescription
)
when {
    principal.role == "pharmacist"
    && !resource.isFilled
    && (
        !resource.isControlled
        || (context has controlledSubstanceVerified && context.controlledSubstanceVerified)
    )
};
