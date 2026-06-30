// FLOOR: listed-customer + OPEN-status accounts MUST be viewable.
// Subset of the viewBalance ceiling (OPEN implies != CLOSED).
permit (
    principal is AccountManager,
    action == Action::"viewBalance",
    resource is BankAccount
)
when {
    principal.accountList.contains(resource.accountHolder.userId)
    && resource.accountStatus == "OPEN"
};
