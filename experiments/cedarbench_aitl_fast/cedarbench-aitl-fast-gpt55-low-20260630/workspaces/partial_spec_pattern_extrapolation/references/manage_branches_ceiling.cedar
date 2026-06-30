// Ceiling: manageBranches is a lead_dev-only privilege (extrapolated
// from "lead_dev extends senior_dev with merge + manage branches").
// senior_dev and junior_dev cannot manage branches.
permit (
    principal is Developer,
    action == Action::"manageBranches",
    resource is CodeArtifact
)
when {
    principal.role == "lead_dev"
};
