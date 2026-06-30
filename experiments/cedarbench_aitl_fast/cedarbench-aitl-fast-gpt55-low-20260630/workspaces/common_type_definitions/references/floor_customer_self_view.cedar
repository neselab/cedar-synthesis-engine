// Floor: a Customer MUST be permitted to view their own contact.
permit (
    principal is Customer,
    action == Action::"viewContact",
    resource is Customer
)
when {
    principal == resource
};
