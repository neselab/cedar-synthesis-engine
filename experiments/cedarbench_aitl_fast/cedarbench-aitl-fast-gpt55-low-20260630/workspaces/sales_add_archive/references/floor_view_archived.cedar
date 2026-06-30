// Floor: viewers MUST still be able to view archived presentations
permit (
    principal is User,
    action == Action::"viewPresentation",
    resource is Presentation
) when {
    resource.isArchived &&
    principal in resource.viewers
};
