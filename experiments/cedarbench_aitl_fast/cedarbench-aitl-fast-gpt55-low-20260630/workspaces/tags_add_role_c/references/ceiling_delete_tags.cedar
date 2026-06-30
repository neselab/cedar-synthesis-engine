permit (
    principal is User,
    action == Action::"DeleteWorkspace",
    resource is Workspace
) when {
    principal in Role::"Role-A" &&
    principal.allowedTagsForRole has "Role-A" &&
    (!(principal.allowedTagsForRole["Role-A"] has production_status && resource.tags has production_status) || (principal.allowedTagsForRole["Role-A"] has production_status && resource.tags has production_status && (principal.allowedTagsForRole["Role-A"]["production_status"].contains("ALL") || resource.tags["production_status"].contains("ALL") || principal.allowedTagsForRole["Role-A"]["production_status"].containsAll(resource.tags["production_status"])))) &&
    (!(principal.allowedTagsForRole["Role-A"] has country && resource.tags has country) || (principal.allowedTagsForRole["Role-A"] has country && resource.tags has country && (principal.allowedTagsForRole["Role-A"]["country"].contains("ALL") || resource.tags["country"].contains("ALL") || principal.allowedTagsForRole["Role-A"]["country"].containsAll(resource.tags["country"])))) &&
    (!(principal.allowedTagsForRole["Role-A"] has stage && resource.tags has stage) || (principal.allowedTagsForRole["Role-A"] has stage && resource.tags has stage && (principal.allowedTagsForRole["Role-A"]["stage"].contains("ALL") || resource.tags["stage"].contains("ALL") || principal.allowedTagsForRole["Role-A"]["stage"].containsAll(resource.tags["stage"]))))
};