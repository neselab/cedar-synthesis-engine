permit (
    principal is User,
    action,
    resource is Workspace
)
when {
    principal in Role::"Role-B" &&
    principal.allowedTagsForRole has "Role-B" &&
    principal.allowedTagsForRole["Role-B"] has production_status &&
    principal.allowedTagsForRole["Role-B"] has country &&
    principal.allowedTagsForRole["Role-B"] has stage &&
    resource.tags has production_status &&
    resource.tags has country &&
    resource.tags has stage &&
    principal.allowedTagsForRole["Role-B"].production_status.containsAll(resource.tags.production_status) &&
    principal.allowedTagsForRole["Role-B"].country.containsAll(resource.tags.country) &&
    principal.allowedTagsForRole["Role-B"].stage.containsAll(resource.tags.stage)
};