// Floor: an Admin MUST be permitted to view any Customer's contact.
permit (
    principal is Admin,
    action == Action::"viewContact",
    resource is Customer
);
