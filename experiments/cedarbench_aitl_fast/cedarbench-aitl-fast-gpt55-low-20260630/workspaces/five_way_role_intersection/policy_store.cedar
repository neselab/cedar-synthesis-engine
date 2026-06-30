// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
permit (
  principal is User,
  action == Action::"read",
  resource is Resource
)
when {
  principal.role == "admin" ||
  principal.secondaryRoles.contains("admin")
};

permit (
  principal is User,
  action == Action::"read",
  resource is Resource
)
when {
  principal.role == "auditor" ||
  principal.secondaryRoles.contains("auditor")
};

permit (
  principal is User,
  action == Action::"read",
  resource is Resource
)
when {
  (principal.role == "developer" ||
   principal.secondaryRoles.contains("developer")) &&
  (resource.category == "code" ||
   resource.category == "logs")
};

permit (
  principal is User,
  action == Action::"read",
  resource is Resource
)
when {
  (principal.role == "qa" ||
   principal.secondaryRoles.contains("qa")) &&
  (resource.category == "code" ||
   resource.category == "tickets")
};

permit (
  principal is User,
  action == Action::"read",
  resource is Resource
)
when {
  (principal.role == "support" ||
   principal.secondaryRoles.contains("support")) &&
  resource.category == "tickets"
};

permit (
  principal is User,
  action == Action::"modify",
  resource is Resource
)
when {
  principal.role == "admin" ||
  principal.secondaryRoles.contains("admin")
};

permit (
  principal is User,
  action == Action::"modify",
  resource is Resource
)
when {
  (principal.role == "developer" ||
   principal.secondaryRoles.contains("developer")) &&
  (resource.category == "code" ||
   resource.category == "config")
};

permit (
  principal is User,
  action == Action::"modify",
  resource is Resource
)
when {
  (principal.role == "qa" ||
   principal.secondaryRoles.contains("qa")) &&
  resource.category == "tickets"
};

permit (
  principal is User,
  action == Action::"delete",
  resource is Resource
)
when {
  principal.role == "admin" ||
  principal.secondaryRoles.contains("admin")
};

permit (
  principal is User,
  action == Action::"audit",
  resource is Resource
)
when {
  principal.role == "auditor" ||
  principal.secondaryRoles.contains("auditor")
};

permit (
  principal is User,
  action == Action::"audit",
  resource is Resource
)
when {
  (principal.role == "developer" ||
   principal.secondaryRoles.contains("developer")) &&
  resource.category == "logs"
};

permit (
  principal is User,
  action == Action::"escalate",
  resource is Resource
)
when {
  principal.role == "support" ||
  principal.secondaryRoles.contains("support")
};

permit (
  principal is User,
  action == Action::"escalate",
  resource is Resource
)
when {
  principal.role == "qa" ||
  principal.secondaryRoles.contains("qa")
};

permit (
  principal is User,
  action == Action::"escalate",
  resource is Resource
)
when {
  principal.role == "developer" ||
  principal.secondaryRoles.contains("developer")
};
