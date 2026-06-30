// Floor: a concrete probe -- a PST employee (timezoneOffset
// == duration("-8h")) at 18:00 UTC has local time 10:00 PST,
// which is inside business hours. They MUST be permitted to
// access the system.
permit (
    principal is Employee,
    action == Action::"access",
    resource is System
)
when {
    principal.timezoneOffset == duration("-8h")
    && context.now == datetime("2025-03-04T18:00:00Z")
};
