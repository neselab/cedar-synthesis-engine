// Ceiling: Auditor may viewDocument only when (serviceline in auditScope
// AND valid consent AND sensitivity constraint). Auditors have view-only
// access — they cannot editDocument per the schema's appliesTo.
permit (
    principal is Taxpreparer::Auditor,
    action == Taxpreparer::Action::"viewDocument",
    resource is Taxpreparer::Document
)
when {
    principal.auditScope.contains(resource.serviceline)
    && context.consent.client == resource.owner
    && context.consent.team_region_list.contains(principal.location)
    && (!resource.isSensitive || context.consent.team_region_list.contains("HQ"))
};
