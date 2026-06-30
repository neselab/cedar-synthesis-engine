// Floor: any Employee whose local time-of-day (after applying
// their timezone offset to context.now) is within business hours
// MUST be permitted to access the system. Local business hours
// are 9:00 inclusive through 17:00 exclusive.
permit (
    principal is Employee,
    action == Action::"access",
    resource is System
)
when {
    context.now.offset(principal.timezoneOffset).toTime() >= duration("9h")
    && context.now.offset(principal.timezoneOffset).toTime() < duration("17h")
};
