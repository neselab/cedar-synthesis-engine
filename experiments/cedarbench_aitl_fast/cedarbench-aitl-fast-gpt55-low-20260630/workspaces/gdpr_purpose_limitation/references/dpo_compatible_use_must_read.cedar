// Floor: a DPO reading PersonalData with consent and a compatible-use
// approval (even if declaredPurpose is NOT in allowedPurposes) MUST be
// permitted to read. Exercises the Art. 6.4 escape hatch.
permit (
    principal is Processor,
    action == Action::"read",
    resource is PersonalData
)
when {
    principal.role == "dpo"
    && resource.subjectConsent
    && context has compatibleUseApproval
    && context.compatibleUseApproval
};
