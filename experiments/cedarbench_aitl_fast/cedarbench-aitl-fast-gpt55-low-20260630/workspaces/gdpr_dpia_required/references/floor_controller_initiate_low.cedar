// Floor: a controller MUST be able to initiate processing on a low-risk
// activity (no DPIA required for low risk).
permit (
    principal is Processor,
    action == Action::"initiateProcessing",
    resource is ProcessingActivity
)
when {
    principal.role == "controller"
    && resource.riskLevel == "low"
};
