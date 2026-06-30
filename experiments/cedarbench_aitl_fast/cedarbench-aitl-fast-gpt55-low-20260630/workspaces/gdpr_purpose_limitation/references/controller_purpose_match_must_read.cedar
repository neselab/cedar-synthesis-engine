// Floor: a controller reading PersonalData with consent and a declared
// purpose in allowedPurposes MUST be permitted to read.
permit (
    principal is Processor,
    action == Action::"read",
    resource is PersonalData
)
when {
    principal.role == "controller"
    && resource.subjectConsent
    && resource.allowedPurposes.contains(context.declaredPurpose)
};
