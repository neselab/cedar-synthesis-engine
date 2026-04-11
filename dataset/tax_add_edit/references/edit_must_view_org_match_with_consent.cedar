// Floor: a Professional MUST be permitted to editDocument when the
// org-match condition AND the consent validity condition both hold.
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
};
