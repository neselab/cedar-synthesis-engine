// Ceiling: read permitted only if
//   - junior_dev whose assignedProject matches resource.project, OR
//   - senior_dev (any project), OR
//   - lead_dev (any project, inherited from senior_dev).
permit (
    principal is Developer,
    action == Action::"read",
    resource is CodeArtifact
)
when {
    (principal.role == "junior_dev" && principal.assignedProject == resource.project)
    || principal.role == "senior_dev"
    || principal.role == "lead_dev"
};
