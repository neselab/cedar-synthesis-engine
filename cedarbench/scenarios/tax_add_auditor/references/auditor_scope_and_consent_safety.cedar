// Ceiling: an Auditor may viewDocument only when BOTH:
//  (a) the document's serviceline is in the auditor's auditScope set; AND
//  (b) the request's consent is valid (consent.client == owner AND
//      consent.team_region_list contains principal.location).
// Auditors bypass organization matching but not consent.
permit (
    principal is Taxpreparer::Auditor,
    action == Taxpreparer::Action::"viewDocument",
    resource is Taxpreparer::Document
)
when {
    principal.auditScope.contains(resource.serviceline)
    && context.consent.client == resource.owner
    && context.consent.team_region_list.contains(principal.location)
};
