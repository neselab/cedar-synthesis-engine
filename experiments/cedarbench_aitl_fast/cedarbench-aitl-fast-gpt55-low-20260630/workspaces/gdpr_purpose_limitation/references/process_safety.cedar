// Ceiling: process permitted only when subject consented AND
// (purpose-match OR compatible-use approval) AND principal is a
// controller or processor (NOT dpo).
permit (
    principal is Processor,
    action == Action::"process",
    resource is PersonalData
)
when {
    resource.subjectConsent
    && (
        resource.allowedPurposes.contains(context.declaredPurpose)
        || (context has compatibleUseApproval && context.compatibleUseApproval)
    )
    && (principal.role == "controller" || principal.role == "processor")
};
