// Floor: any User attempting `withdraw` on an Account whose balance is
// strictly greater than the smallest representable positive decimal
// (0.0001) MUST be permitted. This pins the lower edge of the withdraw
// ceiling, guaranteeing the candidate doesn't accidentally tighten the
// threshold above 0.0001.
permit (
    principal is User,
    action == Action::"withdraw",
    resource is Account
)
when {
    resource.balance.greaterThan(decimal("0.0001"))
};
