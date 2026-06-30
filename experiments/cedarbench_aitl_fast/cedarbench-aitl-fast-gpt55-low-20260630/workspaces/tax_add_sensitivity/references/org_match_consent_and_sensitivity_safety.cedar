// Ceiling: a Professional may viewDocument only when ALL of:
//  (a) org match (assigned_orgs contains matching record),
//  (b) consent is valid (consent.client == owner AND team_region_list
//      contains principal.location),
//  (c) if the document is sensitive, the consent's team_region_list
//      also contains "HQ".
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
