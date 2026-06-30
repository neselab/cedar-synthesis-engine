// CEILING for `closeAccount`. Permitted only when the principal's
// roleType is exactly "manager" and the account balance is exactly
// zero. Note: accountList membership is intentionally NOT required —
// this asymmetry is part of the spec.
permit (
    principal is AccountManager,
    action == Action::"closeAccount",
    resource is BankAccount
)
when {
    principal.roleType == "manager"
    && resource.balance == 0
};
