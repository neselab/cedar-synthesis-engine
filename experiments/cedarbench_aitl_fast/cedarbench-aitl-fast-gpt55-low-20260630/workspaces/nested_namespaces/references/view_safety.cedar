// Ceiling: view permitted only when (issuer) OR (owning team manager)
// OR (same department as issuer).
permit (
    principal is Company::Identity::Employee,
    action == Company::Billing::Invoice::Action::"view",
    resource is Company::Billing::Invoice::Line
)
when {
    principal == resource.issuer
    || principal == resource.owningTeam.manager
    || principal.department == resource.issuer.department
};
