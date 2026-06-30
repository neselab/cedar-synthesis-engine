// FLOOR: listed-customer + FROZEN-status accounts MUST be viewable.
// Subset of the viewBalance ceiling (FROZEN implies != CLOSED).
permit (
    principal is AccountManager,
    action == Action::"viewBalance",
    resource is BankAccount
)
when {
    principal.accountList.contains(resource.accountHolder.userId)
    && resource.accountStatus == "FROZEN"
};
