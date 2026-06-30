// Ceiling: disclose permitted only when subject consented AND
// (purpose-match OR compatible-use approval) AND principal is the DPO.
permit (
    principal is Processor,
    action == Action::"disclose",
    resource is PersonalData
)
when {
    resource.subjectConsent
    && (
        resource.allowedPurposes.contains(context.declaredPurpose)
        || (context has compatibleUseApproval && context.compatibleUseApproval)
    )
    && principal.role == "dpo"
};
