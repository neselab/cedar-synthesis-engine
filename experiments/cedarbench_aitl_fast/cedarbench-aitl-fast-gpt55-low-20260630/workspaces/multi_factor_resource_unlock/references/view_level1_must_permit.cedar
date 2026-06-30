// Floor: any user MUST be able to view a level-1 secret without
// any attestation factors.
permit (
    principal is User,
    action == Action::"view",
    resource is Secret
)
when {
    resource.sensitivityLevel == 1
};
