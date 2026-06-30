// Ceiling: performAction is permitted ONLY when:
//   1. The sign-guard holds (now is at or after lastActionAt), and
//   2. More than 1 hour has elapsed since the last action.
//
// Duration uses Go-style syntax -- "1h", not ISO-8601 "PT1H" (§8.9).
// durationSince returns a SIGNED duration, so the sign-guard is required
// (per spec) to defend against clock-skew bugs.
permit (
    principal is User,
    action == Action::"performAction",
    resource is Resource
)
when {
    context.now >= principal.lastActionAt
    && context.now.durationSince(principal.lastActionAt) > duration("1h")
};
