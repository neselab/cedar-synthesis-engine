// Floor: Professional MUST editDocument when (org match AND valid consent
// AND NOT sensitive).
permit (
    principal is Taxpreparer::Professional,
    action == Taxpreparer::Action::"editDocument",
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
    && !resource.isSensitive
};
