// Floor: a controller MUST be able to initiate processing on a high-risk
// activity when a valid DPIA exists (completed, approved, fresh).
permit (
    principal is Processor,
    action == Action::"initiateProcessing",
    resource is ProcessingActivity
)
when {
    principal.role == "controller"
    && resource.riskLevel == "high"
    && resource has dpiaCompletedDate
    && resource.dpiaApproved
    && context.now.durationSince(resource.dpiaCompletedDate) < duration("365d")
};
