// Ceiling: access is permitted only when the employee's local
// time-of-day is within business hours (9:00 inclusive through
// 17:00 exclusive). Local time-of-day is computed by offsetting
// the supplied UTC datetime by the employee's timezone offset
// and extracting the time-of-day component.
permit (
    principal is Employee,
    action == Action::"access",
    resource is System
)
when {
    context.now.offset(principal.timezoneOffset).toTime() >= duration("9h")
    && context.now.offset(principal.timezoneOffset).toTime() < duration("17h")
};
