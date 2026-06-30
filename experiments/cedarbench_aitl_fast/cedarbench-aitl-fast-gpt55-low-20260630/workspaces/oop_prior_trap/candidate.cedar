permit (
    principal is AccountManager,
    action == Action::"viewBalance",
    resource is BankAccount
)
when {
    principal.accountList.contains(resource.accountHolder.userId) &&
    resource.accountStatus != "CLOSED"
};

permit (
    principal is AccountManager,
    action == Action::"transferFunds",
    resource is BankAccount
)
when {
    principal.accountList.contains(resource.accountHolder.userId) &&
    resource.accountStatus == "OPEN" &&
    resource.balance > 0
};

permit (
    principal is AccountManager,
    action == Action::"closeAccount",
    resource is BankAccount
)
when {
    principal.roleType == "manager" &&
    resource.balance == 0
};