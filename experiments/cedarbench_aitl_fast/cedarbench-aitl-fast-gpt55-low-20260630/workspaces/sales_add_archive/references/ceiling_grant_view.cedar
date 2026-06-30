// Ceiling: grantViewAccessToPresentation — owner or editor, AND not archived
permit (
    principal is User,
    action == Action::"grantViewAccessToPresentation",
    resource is Presentation
) when {
    !resource.isArchived &&
    (resource.owner == principal || principal in resource.editors)
};
