// Ceiling for terminateProcessing: controller or DPO, no DPIA needed.
permit (
    principal is Processor,
    action == Action::"terminateProcessing",
    resource is ProcessingActivity
)
when {
    principal.role == "controller" || principal.role == "dpo"
};
