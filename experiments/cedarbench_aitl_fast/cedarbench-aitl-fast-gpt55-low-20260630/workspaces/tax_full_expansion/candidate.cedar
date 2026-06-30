forbid (
    principal,
    action in [Taxpreparer::Action::"viewDocument", Taxpreparer::Action::"editDocument"],
    resource
)
unless {
    context.consent.client == resource.owner &&
    context.consent.team_region_list.contains(principal.location)
};

forbid (
    principal,
    action in [Taxpreparer::Action::"viewDocument", Taxpreparer::Action::"editDocument"],
    resource
)
when {
    resource.isSensitive == true
}
unless {
    context.consent.team_region_list.contains("HQ")
};

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
};

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
};

permit (
    principal is Taxpreparer::Supervisor,
    action == Taxpreparer::Action::"viewDocument",
    resource is Taxpreparer::Document
)
when {
    principal.supervised_orgs.contains(resource.owner.organization)
};

permit (
    principal is Taxpreparer::Supervisor,
    action == Taxpreparer::Action::"editDocument",
    resource is Taxpreparer::Document
)
when {
    principal.supervised_orgs.contains(resource.owner.organization)
};

permit (
    principal is Taxpreparer::Auditor,
    action == Taxpreparer::Action::"viewDocument",
    resource is Taxpreparer::Document
)
when {
    principal.auditScope.contains(resource.serviceline)
};