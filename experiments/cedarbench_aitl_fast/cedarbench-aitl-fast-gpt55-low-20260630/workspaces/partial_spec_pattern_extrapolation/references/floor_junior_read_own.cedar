// Floor: a junior_dev MUST be permitted to read a CodeArtifact whose
// project equals their assignedProject.
permit (
    principal is Developer,
    action == Action::"read",
    resource is CodeArtifact
)
when {
    principal.role == "junior_dev"
    && principal.assignedProject == resource.project
};
