// Floor: a team manager with level >= 3 MUST be permitted to approve
// a line on their own team when the total is at most 10000.
// No global forbids → no exclusions (§8.8).
permit (
    principal is Company::Identity::Employee,
    action == Company::Billing::Invoice::Action::"approve",
    resource is Company::Billing::Invoice::Line
)
when {
    principal == resource.owningTeam.manager
    && principal.level >= 3
    && resource.total <= 10000
};
