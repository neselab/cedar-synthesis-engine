// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
permit (
  principal is Employee,
  action == Action::"read",
  resource is Resource
) when {
  (principal.level >= 1 && resource.category == "standard") ||
  (principal.level >= 2 && resource.category == "criticalAction") ||
  (principal.level >= 2 && resource.category == "restrictedAction")
};

permit (
  principal is Employee,
  action == Action::"execute",
  resource is Resource
) when {
  (principal.level >= 1 && resource.category == "standard") ||
  (principal.level >= 2 && resource.category == "criticalAction") ||
  (principal.level >= 3 && resource.category == "restrictedAction")
};
