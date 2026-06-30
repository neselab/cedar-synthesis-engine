// Ceiling: view permitted only when the correct factor combination is
// present for the secret's sensitivity level.
//   Level 1 → no factors required.
//   Level 2 → hasMfa.
//   Level 3 → hasMfa AND hasManagerApproval.
permit (
    principal is User,
    action == Action::"view",
    resource is Secret
)
when {
    (resource.sensitivityLevel == 1)
    || (resource.sensitivityLevel == 2 && context.hasMfa)
    || (resource.sensitivityLevel == 3 && context.hasMfa && context.hasManagerApproval)
};
