// Floor: a global-support user with an active session and a non-empty
// ticket ID MUST be permitted to readResource on a cross-tenant
// resource. The `principal.tenant != resource.tenant` clause narrows
// the floor to the cross-tenant case specifically — same-tenant reads
// are covered by the other floor.
permit (
    principal is User,
    action == Action::"readResource",
    resource is Resource
)
when {
    principal.tenant != resource.tenant
    && principal.isGlobalSupport
    && context.supportSessionActive
    && context.ticketId != ""
};
