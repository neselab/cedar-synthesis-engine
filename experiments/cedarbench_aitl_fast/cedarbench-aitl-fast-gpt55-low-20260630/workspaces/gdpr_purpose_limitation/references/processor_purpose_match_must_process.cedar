// Floor: a processor processing PersonalData with consent and a declared
// purpose in allowedPurposes MUST be permitted to process.
permit (
    principal is Processor,
    action == Action::"process",
    resource is PersonalData
)
when {
    principal.role == "processor"
    && resource.subjectConsent
    && resource.allowedPurposes.contains(context.declaredPurpose)
};
