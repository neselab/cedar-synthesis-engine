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
  principal is Taxpreparer::Supervisor,
  action == Taxpreparer::Action::"viewDocument",
  resource is Taxpreparer::Document
)
when {
  principal.supervised_orgs.contains(resource.owner.organization)
};

forbid (
  principal is Taxpreparer::Professional,
  action == Taxpreparer::Action::"viewDocument",
  resource is Taxpreparer::Document
)
unless {
  context.consent.client == resource.owner &&
  context.consent.team_region_list.contains(principal.location)
};

forbid (
  principal is Taxpreparer::Supervisor,
  action == Taxpreparer::Action::"viewDocument",
  resource is Taxpreparer::Document
)
unless {
  context.consent.client == resource.owner &&
  context.consent.team_region_list.contains(principal.location)
};