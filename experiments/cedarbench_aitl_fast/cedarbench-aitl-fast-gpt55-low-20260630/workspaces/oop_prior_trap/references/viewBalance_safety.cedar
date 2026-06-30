// CEILING for `viewBalance`. Permitted only when the manager's
// accountList contains this account's holder's userId AND the
// account is not closed.
permit (
    principal is AccountManager,
    action == Action::"viewBalance",
    resource is BankAccount
)
when {
    principal.accountList.contains(resource.accountHolder.userId)
    && resource.accountStatus != "CLOSED"
};
