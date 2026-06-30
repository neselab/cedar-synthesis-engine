// Floor: user with role "returns_lead" must be permitted to perform action returnOrder.
permit (
    principal is User,
    action == Action::"returnOrder",
    resource is Order
)
when {
    principal.role == "returns_lead"
};
