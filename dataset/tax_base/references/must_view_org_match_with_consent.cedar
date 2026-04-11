// Floor: a Professional MUST be permitted to viewDocument when BOTH the
// org-match condition AND the consent validity condition hold. The base
// policy has no global forbids beyond the consent check, and the consent
// check is already baked into the floor's when clause, so no §8.8
// exclusion is needed.
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
};
