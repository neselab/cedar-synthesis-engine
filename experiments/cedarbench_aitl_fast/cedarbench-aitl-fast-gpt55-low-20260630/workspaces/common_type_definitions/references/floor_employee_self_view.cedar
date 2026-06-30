// Floor: an Employee MUST be permitted to view their own contact.
permit (
    principal is Employee,
    action == Action::"viewContact",
    resource is Employee
)
when {
    principal == resource
};
