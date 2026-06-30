// Floor: a level-5-or-higher team manager MUST be permitted to void a
// line on their own team.
// No global forbids → no exclusions (§8.8).
permit (
    principal is Company::Identity::Employee,
    action == Company::Billing::Invoice::Action::"void",
    resource is Company::Billing::Invoice::Line
)
when {
    principal == resource.owningTeam.manager
    && principal.level >= 5
};
