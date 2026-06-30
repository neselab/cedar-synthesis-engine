// Floor: any user MUST be able to view any proposal. view is fully
// open per the spec.
permit (
    principal is User,
    action == Action::"view",
    resource is Proposal
);
