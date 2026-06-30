// Floor: user with role "compliance_officer" must be permitted to perform action voidTransaction.
permit (
    principal is User,
    action == Action::"voidTransaction",
    resource is Order
)
when {
    principal.role == "compliance_officer"
};
