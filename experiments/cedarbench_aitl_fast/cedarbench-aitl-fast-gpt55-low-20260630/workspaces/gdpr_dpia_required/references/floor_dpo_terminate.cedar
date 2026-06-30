// Floor: the DPO MUST be able to terminate any processing activity,
// regardless of DPIA state — needed to wind down high-risk processing
// even after the DPIA has lapsed.
permit (
    principal is Processor,
    action == Action::"terminateProcessing",
    resource is ProcessingActivity
)
when {
    principal.role == "dpo"
};
