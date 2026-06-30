// Ceiling: verifyAddress is permitted ONLY when the resource's address
// country is "US" (domestic addresses only). This exercises nested
// access through the common type alias: resource.contact.address.country.
permit (
    principal is Admin,
    action == Action::"verifyAddress",
    resource
)
when {
    resource.contact.address.country == "US"
};
