// Ceiling: void permitted only when the principal is the owning team's
// manager AND their level is at least 5.
permit (
    principal is Company::Identity::Employee,
    action == Company::Billing::Invoice::Action::"void",
    resource is Company::Billing::Invoice::Line
)
when {
    principal == resource.owningTeam.manager
    && principal.level >= 5
};
