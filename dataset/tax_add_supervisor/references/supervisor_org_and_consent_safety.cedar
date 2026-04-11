// Ceiling: a Supervisor may viewDocument only when BOTH:
//  (a) the document's owner organization is in principal.supervised_orgs;
//  (b) the consent is valid (consent.client == owner AND
//      consent.team_region_list contains principal.location).
permit (
    principal is Taxpreparer::Supervisor,
    action == Taxpreparer::Action::"viewDocument",
    resource is Taxpreparer::Document
)
when {
    principal.supervised_orgs.contains(resource.owner.organization)
    && context.consent.client == resource.owner
    && context.consent.team_region_list.contains(principal.location)
};
