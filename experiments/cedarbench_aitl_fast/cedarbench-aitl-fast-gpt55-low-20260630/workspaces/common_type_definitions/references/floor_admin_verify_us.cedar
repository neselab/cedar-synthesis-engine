// Floor: an Admin MUST be permitted to verify a Customer with a US address.
// Exercises nested record access through common type alias.
permit (
    principal is Admin,
    action == Action::"verifyAddress",
    resource is Customer
)
when {
    resource.contact.address.country == "US"
};
