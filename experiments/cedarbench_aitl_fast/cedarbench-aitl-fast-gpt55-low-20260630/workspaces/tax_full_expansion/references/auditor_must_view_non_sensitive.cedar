// Floor: Auditor MUST viewDocument when (auditScope contains serviceline
// AND valid consent AND NOT sensitive).
permit (
    principal is Taxpreparer::Auditor,
    action == Taxpreparer::Action::"viewDocument",
    resource is Taxpreparer::Document
)
when {
    principal.auditScope.contains(resource.serviceline)
    && context.consent.client == resource.owner
    && context.consent.team_region_list.contains(principal.location)
    && !resource.isSensitive
};
