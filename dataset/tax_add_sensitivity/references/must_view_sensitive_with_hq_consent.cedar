// Floor: a Professional MUST be permitted to viewDocument for a sensitive
// document when the org match holds, the consent is valid, AND the
// consent's team_region_list contains "HQ".
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
    && resource.isSensitive
    && context.consent.team_region_list.contains("HQ")
};
