// Ceiling: access permitted only when ALL FIVE orthogonal conditions hold.
//   1. principal not blocked
//   2. resource not archived
//   3. MFA gate satisfied (resource doesn't require MFA, or principal has it)
//   4. inside business hours
//   5. not rate-limited
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    !principal.isBlocked
    && !resource.isArchived
    && (!resource.requiresMfa || principal.mfaVerified)
    && !context.outsideBusinessHours
    && !context.rateLimited
};
