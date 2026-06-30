// Floor: a Customer MUST be permitted to update their own contact.
permit (
    principal is Customer,
    action == Action::"updateContact",
    resource is Customer
)
when {
    principal == resource
};
