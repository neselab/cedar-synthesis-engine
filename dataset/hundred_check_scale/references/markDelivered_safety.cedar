// Ceiling: markDelivered permitted only for the listed roles and statuses.
permit (
    principal is User,
    action == Action::"markDelivered",
    resource is Order
)
when {
    (principal.role == "fulfillment" || principal.role == "warehouse_lead")
    && (resource.status == "shipped")
};
