// Floor: a non-admin member MUST be permitted to read a document in
// their own tenant when the tenant is NOT in default-deny mode.
//
// §8.8 floor-bound consistency: cross-tenant is unconditionally
// forbidden, but the same-tenant + !defaultDeny condition trivially
// excludes that. Admins pass too. This floor only asserts the member
// case.
permit (
    principal is User,
    action == Action::"read",
    resource is Document
)
when {
    principal.tenant == resource.tenant
    && !principal.tenant.defaultDeny
    && principal.role == "member"
};
