// Floor: an owner MUST be able to read their own resource. The owner
// bypass is unconditional with respect to the attestation flags — owners
// are the root of the grant chain and are never cascade-invalidated.
permit (
    principal is User,
    action == Action::"read",
    resource is Resource
)
when {
    principal == resource.owner
};
