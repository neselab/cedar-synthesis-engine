// Ceiling: a Professional may viewDocument only when BOTH:
//  (a) there exists an assignment in principal.assigned_orgs whose
//      organization, serviceline, and location match the document's
//      owner.organization, document.serviceline, and document.location
//      respectively; AND
//  (b) the request's consent is valid: consent.client == resource.owner
//      AND consent.team_region_list contains principal.location.
//
// The base scenario has no ad-hoc template-linked permits, so this is the
// only permit path. Entity types are qualified with the Taxpreparer namespace.
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
