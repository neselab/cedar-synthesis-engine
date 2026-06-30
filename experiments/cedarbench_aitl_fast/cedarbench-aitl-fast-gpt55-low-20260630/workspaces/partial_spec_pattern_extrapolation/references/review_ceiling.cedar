// Ceiling: review permitted only for senior_dev or lead_dev
// (lead_dev inherits review from senior_dev). junior_dev cannot review.
permit (
    principal is Developer,
    action == Action::"review",
    resource is CodeArtifact
)
when {
    principal.role == "senior_dev"
    || principal.role == "lead_dev"
};
