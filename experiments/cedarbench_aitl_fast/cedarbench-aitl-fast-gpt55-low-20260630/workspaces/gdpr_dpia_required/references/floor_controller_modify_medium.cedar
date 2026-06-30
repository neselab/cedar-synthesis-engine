// Floor: a controller MUST be able to modify a medium-risk processing
// activity (no DPIA required for medium risk).
permit (
    principal is Processor,
    action == Action::"modifyProcessing",
    resource is ProcessingActivity
)
when {
    principal.role == "controller"
    && resource.riskLevel == "medium"
};
