permit (
  principal is Individual,
  action == Action::"access",
  resource is Resource
)
when {
  principal in resource.parentOrg
};