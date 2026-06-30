// Floor: any Employee MUST be permitted to perform the report
// action on a System resource at any time of day, regardless of
// timezone or local time-of-day.
permit (
    principal is Employee,
    action == Action::"report",
    resource is System
);
