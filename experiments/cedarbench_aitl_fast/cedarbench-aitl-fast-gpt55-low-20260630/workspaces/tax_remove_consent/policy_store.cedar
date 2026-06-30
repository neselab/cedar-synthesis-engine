// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
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
