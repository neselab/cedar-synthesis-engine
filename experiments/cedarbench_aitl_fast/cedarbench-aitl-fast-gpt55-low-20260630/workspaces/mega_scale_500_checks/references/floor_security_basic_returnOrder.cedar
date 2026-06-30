// Floor: user with role "security_basic" must be permitted to perform action returnOrder.
permit (
    principal is User,
    action == Action::"returnOrder",
    resource is Order
)
when {
    principal.role == "security_basic"
};
