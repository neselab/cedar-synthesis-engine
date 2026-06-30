// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
permit (
  principal is User,
  action == Action::"Search",
  resource is Document
);

permit (
  principal is User,
  action == Action::"View",
  resource is Document
)
when {
  principal.auditCleared
};

permit (
  principal is User,
  action == Action::"Edit",
  resource is Document
)
when {
  principal.auditCleared
};

permit (
  principal is User,
  action == Action::"Delete",
  resource is Document
)
when {
  principal.auditCleared && principal.role == "admin"
};
