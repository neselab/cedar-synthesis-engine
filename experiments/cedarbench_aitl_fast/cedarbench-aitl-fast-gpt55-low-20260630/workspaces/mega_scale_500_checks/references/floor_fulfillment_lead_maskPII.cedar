// Floor: user with role "fulfillment_lead" must be permitted to perform action maskPII.
permit (
    principal is User,
    action == Action::"maskPII",
    resource is Order
)
when {
    principal.role == "fulfillment_lead"
};
