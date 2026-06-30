// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
permit (
  principal is Individual,
  action == Action::"access",
  resource is Resource
)
when {
  principal in resource.parentOrg
};
