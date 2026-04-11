// Floor: a Professional MUST be permitted to viewDocument when the
// org-match condition holds. No consent check needed.
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
