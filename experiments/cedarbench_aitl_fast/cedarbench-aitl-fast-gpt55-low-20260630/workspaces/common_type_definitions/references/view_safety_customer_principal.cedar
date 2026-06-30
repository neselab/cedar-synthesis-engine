// Ceiling: when a Customer is the principal viewing a Customer/Vendor/Employee,
// view is permitted ONLY if principal == resource (own contact).
// Customers have no admin authority.
permit (
    principal is Customer,
    action == Action::"viewContact",
    resource
)
when {
    principal == resource
};
