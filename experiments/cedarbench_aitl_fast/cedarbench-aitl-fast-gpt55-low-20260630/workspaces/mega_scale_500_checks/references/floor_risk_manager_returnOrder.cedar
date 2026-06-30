// Floor: user with role "risk_manager" must be permitted to perform action returnOrder.
permit (
    principal is User,
    action == Action::"returnOrder",
    resource is Order
)
when {
    principal.role == "risk_manager"
};
