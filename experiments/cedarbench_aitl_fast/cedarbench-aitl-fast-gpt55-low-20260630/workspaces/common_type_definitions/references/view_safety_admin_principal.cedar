// Ceiling: when an Admin is the principal, viewing any
// Customer/Vendor/Employee contact is permitted (admin authority).
permit (
    principal is Admin,
    action == Action::"viewContact",
    resource
);
