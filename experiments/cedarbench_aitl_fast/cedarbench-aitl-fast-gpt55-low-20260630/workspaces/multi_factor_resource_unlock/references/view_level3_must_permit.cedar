// Floor: any user with hasMfa AND hasManagerApproval MUST be able
// to view a level-3 secret.
permit (
    principal is User,
    action == Action::"view",
    resource is Secret
)
when {
    resource.sensitivityLevel == 3
    && context.hasMfa
    && context.hasManagerApproval
};
