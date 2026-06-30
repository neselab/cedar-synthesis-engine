// Floor: user with role "fulfillment_lead" must be permitted to perform action adminOverride.
permit (
    principal is User,
    action == Action::"adminOverride",
    resource is Order
)
when {
    principal.role == "fulfillment_lead"
};
