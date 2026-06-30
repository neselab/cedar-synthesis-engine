// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
permit (
  principal is User,
  action == Action::"read",
  resource is Document
)
when {
  principal == resource.owner
};
