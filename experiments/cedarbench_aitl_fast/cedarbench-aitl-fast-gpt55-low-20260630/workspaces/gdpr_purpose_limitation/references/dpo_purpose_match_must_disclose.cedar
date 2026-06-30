// Floor: a DPO disclosing PersonalData with consent and a declared
// purpose in allowedPurposes MUST be permitted to disclose. Only the
// DPO is permitted to disclose under this policy.
permit (
    principal is Processor,
    action == Action::"disclose",
    resource is PersonalData
)
when {
    principal.role == "dpo"
    && resource.subjectConsent
    && resource.allowedPurposes.contains(context.declaredPurpose)
};
