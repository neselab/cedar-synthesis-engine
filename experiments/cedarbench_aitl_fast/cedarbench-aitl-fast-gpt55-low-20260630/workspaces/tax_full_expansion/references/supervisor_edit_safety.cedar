// Ceiling: Supervisor may editDocument only when (owner.organization in
// supervised_orgs AND valid consent AND sensitivity constraint).
permit (
    principal is Taxpreparer::Supervisor,
    action == Taxpreparer::Action::"editDocument",
    resource is Taxpreparer::Document
)
when {
    principal.supervised_orgs.contains(resource.owner.organization)
    && context.consent.client == resource.owner
    && context.consent.team_region_list.contains(principal.location)
    && (!resource.isSensitive || context.consent.team_region_list.contains("HQ"))
};
