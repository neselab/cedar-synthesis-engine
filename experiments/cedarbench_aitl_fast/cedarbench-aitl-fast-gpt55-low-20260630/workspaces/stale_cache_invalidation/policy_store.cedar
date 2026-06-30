// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
permit (
  principal is User,
  action == Action::"read",
  resource is Resource
)
when {
  context has authCacheTimestamp &&
  context.now.durationSince(context.authCacheTimestamp) < duration("5m")
};

permit (
  principal is User,
  action == Action::"writeCritical",
  resource is Resource
)
when {
  context has authCacheTimestamp &&
  context.now.durationSince(context.authCacheTimestamp) < duration("60s")
};

permit (
  principal is User,
  action == Action::"delete",
  resource is Resource
)
when {
  principal.role == "admin" &&
  context has mfaTimestamp &&
  context.now.durationSince(context.mfaTimestamp) < duration("30s")
};
