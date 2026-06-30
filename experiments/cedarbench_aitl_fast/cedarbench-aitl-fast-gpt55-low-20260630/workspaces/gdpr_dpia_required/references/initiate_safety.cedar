// Ceiling for initiateProcessing: only controllers, and high-risk requires
// a valid (completed, approved, non-stale) DPIA.
permit (
    principal is Processor,
    action == Action::"initiateProcessing",
    resource is ProcessingActivity
)
when {
    principal.role == "controller"
    && (
        resource.riskLevel == "low"
        || resource.riskLevel == "medium"
        || (
            resource.riskLevel == "high"
            && resource has dpiaCompletedDate
            && resource.dpiaApproved
            && context.now.durationSince(resource.dpiaCompletedDate) < duration("365d")
        )
    )
};
