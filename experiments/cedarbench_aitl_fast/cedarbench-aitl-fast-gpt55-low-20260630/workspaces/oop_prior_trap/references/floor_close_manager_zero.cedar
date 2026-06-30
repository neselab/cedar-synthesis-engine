// FLOOR: manager closing a zero-balance account MUST be permitted.
// Identical to the closeAccount ceiling.
permit (
    principal is AccountManager,
    action == Action::"closeAccount",
    resource is BankAccount
)
when {
    principal.roleType == "manager"
    && resource.balance == 0
};
