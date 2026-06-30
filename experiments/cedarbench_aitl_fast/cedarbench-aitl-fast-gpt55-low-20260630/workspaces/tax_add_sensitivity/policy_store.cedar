// Policy store — verified policies appended here

// --- Verified (eval iteration 3) ---
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
  principal is Taxpreparer::Professional,
  action == Taxpreparer::Action::"viewDocument",
  resource is Taxpreparer::Document
)
when {
  resource.isSensitive
}
unless {
  context.consent.team_region_list.contains("HQ")
};
