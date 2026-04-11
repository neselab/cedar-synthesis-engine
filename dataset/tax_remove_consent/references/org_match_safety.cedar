// Ceiling: a Professional may viewDocument only when the org-match
// condition holds. There is NO consent enforcement in this variant.
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
