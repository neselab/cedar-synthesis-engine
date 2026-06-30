// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
permit (
  principal is User,
  action == Action::"view",
  resource is Document
)
when {
  (principal.role == "reader" || principal.role == "admin") &&
  principal.mfaVerified == true &&
  principal == resource.owner
};
