// Ceiling: editPresentation — owner or editor, AND not archived
permit (
    principal is User,
    action == Action::"editPresentation",
    resource is Presentation
) when {
    !resource.isArchived &&
    (resource.owner == principal || principal in resource.editors)
};
