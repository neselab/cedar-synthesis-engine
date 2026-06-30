// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
permit (
  principal is User,
  action == Action::"viewProfile",
  resource is Profile
)
when {
  principal == resource.owner
};
