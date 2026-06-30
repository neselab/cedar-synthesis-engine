// Ceiling: approve permitted only when one of two tiers applies.
//   Tier 1: team manager, level >= 3, total <= 10000
//   Tier 2: level >= 5, total <= 100000
permit (
    principal is Company::Identity::Employee,
    action == Company::Billing::Invoice::Action::"approve",
    resource is Company::Billing::Invoice::Line
)
when {
    (
        principal == resource.owningTeam.manager
        && principal.level >= 3
        && resource.total <= 10000
    )
    || (
        principal.level >= 5
        && resource.total <= 100000
    )
};
