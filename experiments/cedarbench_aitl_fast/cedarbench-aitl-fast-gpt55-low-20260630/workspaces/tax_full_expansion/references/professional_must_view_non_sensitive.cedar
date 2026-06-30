// Floor: Professional MUST viewDocument when (org match AND valid consent
// AND NOT sensitive). Non-sensitive sidesteps the sensitivity forbid per §8.8.
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
    && !resource.isSensitive
};
