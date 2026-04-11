// Ceiling: shipOrder permitted only for the listed roles and statuses.
permit (
    principal is User,
    action == Action::"shipOrder",
    resource is Order
)
when {
    (principal.role == "fulfillment" || principal.role == "warehouse_lead")
    && (resource.status == "pending")
};
