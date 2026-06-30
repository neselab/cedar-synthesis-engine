// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
permit (
  principal is User,
  action == Action::"accessWithGrace",
  resource is Resource
)
when {
  context.now >= principal.graceStart
  &&
  principal.graceQuotaUsed.toMilliseconds() >= 0
  &&
  principal.graceQuotaUsed.toMilliseconds()
    + context.now.durationSince(principal.graceStart).toMilliseconds()
    <= duration("90d").toMilliseconds()
};
