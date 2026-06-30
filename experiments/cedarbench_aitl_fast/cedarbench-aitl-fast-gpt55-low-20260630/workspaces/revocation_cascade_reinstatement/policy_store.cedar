// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
permit (
  principal is User,
  action == Action::"read",
  resource is Resource
)
when {
  principal == resource.owner
};

permit (
  principal is User,
  action == Action::"read",
  resource is Resource
)
when {
  context.accessAuthorized == true &&
  context.revocationDetected == false
};
