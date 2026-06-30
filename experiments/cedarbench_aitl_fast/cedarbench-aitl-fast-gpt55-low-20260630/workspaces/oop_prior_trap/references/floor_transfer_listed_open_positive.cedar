// FLOOR: happy-path transfer must work. Subset of transferFunds
// ceiling — same conjunction.
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
