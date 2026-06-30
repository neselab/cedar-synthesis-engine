// Floor: the issuer MUST always be permitted to view their own line.
// There are no global forbids, so this floor has no exclusions (§8.8).
permit (
    principal is Company::Identity::Employee,
    action == Company::Billing::Invoice::Action::"view",
    resource is Company::Billing::Invoice::Line
)
when {
    principal == resource.issuer
};
