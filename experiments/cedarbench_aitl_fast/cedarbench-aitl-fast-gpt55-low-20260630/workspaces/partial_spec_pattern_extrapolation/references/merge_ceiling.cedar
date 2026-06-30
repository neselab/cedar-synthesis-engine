// Ceiling: merge is a lead_dev-only privilege (extrapolated from
// "lead_dev extends senior_dev with merge + manage branches").
// senior_dev and junior_dev cannot merge.
permit (
    principal is Developer,
    action == Action::"merge",
    resource is CodeArtifact
)
when {
    principal.role == "lead_dev"
};
