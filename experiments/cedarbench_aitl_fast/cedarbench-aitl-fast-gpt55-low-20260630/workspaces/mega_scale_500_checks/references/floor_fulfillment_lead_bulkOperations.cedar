// Floor: user with role "fulfillment_lead" must be permitted to perform action bulkOperations.
permit (
    principal is User,
    action == Action::"bulkOperations",
    resource is Order
)
when {
    principal.role == "fulfillment_lead"
};
