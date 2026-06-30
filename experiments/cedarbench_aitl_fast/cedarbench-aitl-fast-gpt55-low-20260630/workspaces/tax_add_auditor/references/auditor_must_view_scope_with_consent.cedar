// Floor: an Auditor MUST be permitted to viewDocument when the document's
// serviceline is in their auditScope AND the consent is valid.
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
