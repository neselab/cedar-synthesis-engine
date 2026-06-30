// Floor: user with role "fulfillment_lead" must be permitted to perform action applyDiscount.
permit (
    principal is User,
    action == Action::"applyDiscount",
    resource is Order
)
when {
    principal.role == "fulfillment_lead"
};
