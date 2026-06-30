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

forbid (
  principal is Taxpreparer::Professional,
  action,
  resource is Taxpreparer::Document
)
when {
  action == Taxpreparer::Action::"viewDocument" ||
  action == Taxpreparer::Action::"editDocument"
}
unless {
  context.consent.client == resource.owner &&
  context.consent.team_region_list.contains(principal.location)
};