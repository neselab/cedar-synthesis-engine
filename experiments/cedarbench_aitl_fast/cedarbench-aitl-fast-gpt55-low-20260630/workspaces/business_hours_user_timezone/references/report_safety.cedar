// Ceiling: report is permitted for any Employee on any System with
// no time-of-day restriction. The ceiling here just constrains the
// shape (Employee performing report on System) -- the actual policy
// has no time-of-day restriction beyond Cedar's default deny.
permit (
    principal is Employee,
    action == Action::"report",
    resource is System
);
