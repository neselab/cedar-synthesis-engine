// Ceiling: edit permitted only for editor or manager.
// auditAdmin is INTENTIONALLY excluded — the auditor role observes,
// it does not modify. (Counterintuitive: admin != superset.)
permit (
    principal is Worker,
    action == Action::"edit",
    resource is Record
)
when {
    principal.role == "editor"
    || principal.role == "manager"
};
