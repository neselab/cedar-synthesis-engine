// Floor: user with role "cs_agent" must be permitted to perform action returnOrder.
permit (
    principal is User,
    action == Action::"returnOrder",
    resource is Order
)
when {
    principal.role == "cs_agent"
};
