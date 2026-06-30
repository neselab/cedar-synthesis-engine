// Floor: user with role "finance_director" must be permitted to perform action returnOrder.
permit (
    principal is User,
    action == Action::"returnOrder",
    resource is Order
)
when {
    principal.role == "finance_director"
};
