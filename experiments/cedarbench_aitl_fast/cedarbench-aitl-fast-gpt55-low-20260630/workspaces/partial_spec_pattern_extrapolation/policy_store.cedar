// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
permit (
  principal is Developer,
  action == Action::"read",
  resource is CodeArtifact
)
when {
  principal.role == "junior_dev" &&
  resource.project == principal.assignedProject
};

permit (
  principal is Developer,
  action == Action::"write",
  resource is CodeArtifact
)
when {
  principal.role == "junior_dev" &&
  resource.project == principal.assignedProject
};

permit (
  principal is Developer,
  action == Action::"read",
  resource is CodeArtifact
)
when {
  principal.role == "senior_dev" ||
  principal.role == "lead_dev"
};

permit (
  principal is Developer,
  action == Action::"write",
  resource is CodeArtifact
)
when {
  principal.role == "senior_dev" ||
  principal.role == "lead_dev"
};

permit (
  principal is Developer,
  action == Action::"review",
  resource is CodeArtifact
)
when {
  principal.role == "senior_dev" ||
  principal.role == "lead_dev"
};

permit (
  principal is Developer,
  action == Action::"merge",
  resource is CodeArtifact
)
when {
  principal.role == "lead_dev"
};

permit (
  principal is Developer,
  action == Action::"manageBranches",
  resource is CodeArtifact
)
when {
  principal.role == "lead_dev"
};
