// Floor: a Worker with role "auditAdmin" MUST be permitted to view
// any Record. This is the counterintuitive load-bearing floor: the
// auditor role's defining capability is broad VIEW access for oversight.
permit (
    principal is Worker,
    action == Action::"view",
    resource is Record
)
when {
    principal.role == "auditAdmin"
};
