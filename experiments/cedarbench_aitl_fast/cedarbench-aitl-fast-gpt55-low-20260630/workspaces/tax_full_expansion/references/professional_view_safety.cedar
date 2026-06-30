// Ceiling: Professional may viewDocument only when (org match AND valid
// consent AND (!isSensitive OR "HQ" in team_region_list)).
permit (
    principal is Taxpreparer::Professional,
    action == Taxpreparer::Action::"viewDocument",
    resource is Taxpreparer::Document
)
when {
    principal.assigned_orgs.contains({
        organization: resource.owner.organization,
        serviceline: resource.serviceline,
        location: resource.location
    })
    && context.consent.client == resource.owner
    && context.consent.team_region_list.contains(principal.location)
    && (!resource.isSensitive || context.consent.team_region_list.contains("HQ"))
};
