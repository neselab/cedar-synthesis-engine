permit (
  principal is Operator,
  action == Action::"backup",
  resource is System
)
when {
  principal.role == "engineer" ||
  principal.role == "sre" ||
  principal.role == "admin"
};

permit (
  principal is Operator,
  action == Action::"restore",
  resource is System
)
when {
  resource.environment == "staging" &&
  (principal.role == "sre" || principal.role == "admin")
};

permit (
  principal is Operator,
  action == Action::"restore",
  resource is System
)
when {
  resource.environment == "production" &&
  (
    principal.role == "admin" ||
    (principal.role == "sre" && principal.isOnCall == true)
  )
};

permit (
  principal is Operator,
  action == Action::"verify",
  resource is System
)
when {
  principal.role == "engineer" ||
  principal.role == "sre" ||
  principal.role == "admin"
};