// Ceiling: a Customer principal may update contact ONLY for their own
// record. No admin override on update.
permit (
    principal is Customer,
    action == Action::"updateContact",
    resource
)
when {
    principal == resource
};
