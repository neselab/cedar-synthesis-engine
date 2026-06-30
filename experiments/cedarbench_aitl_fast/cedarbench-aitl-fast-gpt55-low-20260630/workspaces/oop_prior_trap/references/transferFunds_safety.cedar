// CEILING for `transferFunds`. Permitted only when the manager's
// accountList contains this account's holder's userId, the account
// status is exactly "OPEN", and the balance is strictly positive.
permit (
    principal is AccountManager,
    action == Action::"transferFunds",
    resource is BankAccount
)
when {
    principal.accountList.contains(resource.accountHolder.userId)
    && resource.accountStatus == "OPEN"
    && resource.balance > 0
};
