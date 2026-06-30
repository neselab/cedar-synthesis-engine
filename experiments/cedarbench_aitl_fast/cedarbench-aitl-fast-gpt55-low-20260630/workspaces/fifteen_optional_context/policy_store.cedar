// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
permit (
  principal is User,
  action == Action::"accessFederatedResource",
  resource is Resource
)
when {
  context has mfaToken &&
  context.mfaToken == true &&
  context has deviceTrusted &&
  context.deviceTrusted == true &&
  context has locationVerified &&
  context.locationVerified == true &&
  context has identityProofed &&
  context.identityProofed == true &&
  context has auditLoggingEnabled &&
  context.auditLoggingEnabled == true
};
