permit (
    principal is User,
    action == Action::"ArchiveWorkspace",
    resource is Workspace
) when {
    principal in Role::"Role-C" &&
    principal.allowedTagsForRole has "Role-C" &&
    (!(principal.allowedTagsForRole["Role-C"] has production_status && resource.tags has production_status) || (principal.allowedTagsForRole["Role-C"] has production_status && resource.tags has production_status && (principal.allowedTagsForRole["Role-C"]["production_status"].contains("ALL") || resource.tags["production_status"].contains("ALL") || principal.allowedTagsForRole["Role-C"]["production_status"].containsAll(resource.tags["production_status"])))) &&
    (!(principal.allowedTagsForRole["Role-C"] has country && resource.tags has country) || (principal.allowedTagsForRole["Role-C"] has country && resource.tags has country && (principal.allowedTagsForRole["Role-C"]["country"].contains("ALL") || resource.tags["country"].contains("ALL") || principal.allowedTagsForRole["Role-C"]["country"].containsAll(resource.tags["country"])))) &&
    (!(principal.allowedTagsForRole["Role-C"] has stage && resource.tags has stage) || (principal.allowedTagsForRole["Role-C"] has stage && resource.tags has stage && (principal.allowedTagsForRole["Role-C"]["stage"].contains("ALL") || resource.tags["stage"].contains("ALL") || principal.allowedTagsForRole["Role-C"]["stage"].containsAll(resource.tags["stage"]))))
};