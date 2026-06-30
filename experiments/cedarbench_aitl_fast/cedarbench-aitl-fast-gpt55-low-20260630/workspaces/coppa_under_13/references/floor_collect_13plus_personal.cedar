// Floor: collecting personal data for a user who is at least 13
// (>= 4748 days old, conservative leap-year-safe threshold) MUST be
// permitted. COPPA does not apply once the data subject is 13+.
// No parental consent is required.
permit (
    principal is User,
    action == Action::"collect",
    resource is DataPoint
)
when {
    resource.category == "personal"
    && context.now.durationSince(principal.dateOfBirth) >= duration("4748d")
};
