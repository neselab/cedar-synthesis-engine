// Ceiling: read permitted only when subject has consented AND
// (purpose-match OR compatible-use approval present and true).
// Note the positive has-guard for the optional compatibleUseApproval —
// avoids the §8.3 negated-has trap.
permit (
    principal is Processor,
    action == Action::"read",
    resource is PersonalData
)
when {
    resource.subjectConsent
    && (
        resource.allowedPurposes.contains(context.declaredPurpose)
        || (context has compatibleUseApproval && context.compatibleUseApproval)
    )
};
