// Ceiling: readResource permitted for public resources unconditionally,
// for internal resources to employee-domain users, for partner
// resources to partner-subdomain users.
permit (
    principal is User,
    action == Action::"readResource",
    resource is Resource
)
when {
    resource.classification == "public"
    || (resource.classification == "internal" && principal.email like "*@example.com")
    || (resource.classification == "partner" && principal.email like "*@partner.example.com")
};
