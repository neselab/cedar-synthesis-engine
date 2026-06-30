permit (
    principal,
    action == Action::"initiateProcessing",
    resource
)
when {
    principal is Processor
    && resource is ProcessingActivity
    && principal.role == "controller"
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

permit (
    principal,
    action == Action::"modifyProcessing",
    resource
)
when {
    principal is Processor
    && resource is ProcessingActivity
    && principal.role == "controller"
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

permit (
    principal,
    action == Action::"terminateProcessing",
    resource
)
when {
    principal is Processor
    && resource is ProcessingActivity
    && (
        principal.role == "controller"
        || principal.role == "dpo"
    )
};