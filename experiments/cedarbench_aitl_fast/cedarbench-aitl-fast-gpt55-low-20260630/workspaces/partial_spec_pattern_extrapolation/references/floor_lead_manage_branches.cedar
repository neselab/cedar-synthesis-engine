// Floor: a lead_dev MUST be permitted to manageBranches on any
// CodeArtifact. This is the second extrapolated permission from
// the spec's lead_dev delta.
permit (
    principal is Developer,
    action == Action::"manageBranches",
    resource is CodeArtifact
)
when {
    principal.role == "lead_dev"
};
