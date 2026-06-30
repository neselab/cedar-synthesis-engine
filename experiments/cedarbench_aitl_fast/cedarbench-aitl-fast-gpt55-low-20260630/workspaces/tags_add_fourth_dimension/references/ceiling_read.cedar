permit (
    principal is User,
    action == Action::"ReadWorkspace",
    resource is Workspace
)
when {
    (
        principal in Role::"role-a" &&
        (
            !(principal.allowedTagsForRole has "Role-A" && principal.allowedTagsForRole["Role-A"] has production_status && resource.tags has production_status) ||
            (principal.allowedTagsForRole has "Role-A" && principal.allowedTagsForRole["Role-A"] has production_status && resource.tags has production_status &&
                (principal.allowedTagsForRole["Role-A"].production_status.contains("ALL") || resource.tags.production_status.contains("ALL") || principal.allowedTagsForRole["Role-A"].production_status.containsAll(resource.tags.production_status)))
        ) &&
        (
            !(principal.allowedTagsForRole has "Role-A" && principal.allowedTagsForRole["Role-A"] has country && resource.tags has country) ||
            (principal.allowedTagsForRole has "Role-A" && principal.allowedTagsForRole["Role-A"] has country && resource.tags has country &&
                (principal.allowedTagsForRole["Role-A"].country.contains("ALL") || resource.tags.country.contains("ALL") || principal.allowedTagsForRole["Role-A"].country.containsAll(resource.tags.country)))
        ) &&
        (
            !(principal.allowedTagsForRole has "Role-A" && principal.allowedTagsForRole["Role-A"] has stage && resource.tags has stage) ||
            (principal.allowedTagsForRole has "Role-A" && principal.allowedTagsForRole["Role-A"] has stage && resource.tags has stage &&
                (principal.allowedTagsForRole["Role-A"].stage.contains("ALL") || resource.tags.stage.contains("ALL") || principal.allowedTagsForRole["Role-A"].stage.containsAll(resource.tags.stage)))
        ) &&
        (
            !(principal.allowedTagsForRole has "Role-A" && principal.allowedTagsForRole["Role-A"] has department && resource.tags has department) ||
            (principal.allowedTagsForRole has "Role-A" && principal.allowedTagsForRole["Role-A"] has department && resource.tags has department &&
                (principal.allowedTagsForRole["Role-A"].department.contains("ALL") || resource.tags.department.contains("ALL") || principal.allowedTagsForRole["Role-A"].department.containsAll(resource.tags.department)))
        )
    ) ||
    (
        principal in Role::"role-b" &&
        (
            !(principal.allowedTagsForRole has "Role-B" && principal.allowedTagsForRole["Role-B"] has production_status && resource.tags has production_status) ||
            (principal.allowedTagsForRole has "Role-B" && principal.allowedTagsForRole["Role-B"] has production_status && resource.tags has production_status &&
                (principal.allowedTagsForRole["Role-B"].production_status.contains("ALL") || resource.tags.production_status.contains("ALL") || principal.allowedTagsForRole["Role-B"].production_status.containsAll(resource.tags.production_status)))
        ) &&
        (
            !(principal.allowedTagsForRole has "Role-B" && principal.allowedTagsForRole["Role-B"] has country && resource.tags has country) ||
            (principal.allowedTagsForRole has "Role-B" && principal.allowedTagsForRole["Role-B"] has country && resource.tags has country &&
                (principal.allowedTagsForRole["Role-B"].country.contains("ALL") || resource.tags.country.contains("ALL") || principal.allowedTagsForRole["Role-B"].country.containsAll(resource.tags.country)))
        ) &&
        (
            !(principal.allowedTagsForRole has "Role-B" && principal.allowedTagsForRole["Role-B"] has stage && resource.tags has stage) ||
            (principal.allowedTagsForRole has "Role-B" && principal.allowedTagsForRole["Role-B"] has stage && resource.tags has stage &&
                (principal.allowedTagsForRole["Role-B"].stage.contains("ALL") || resource.tags.stage.contains("ALL") || principal.allowedTagsForRole["Role-B"].stage.containsAll(resource.tags.stage)))
        ) &&
        (
            !(principal.allowedTagsForRole has "Role-B" && principal.allowedTagsForRole["Role-B"] has department && resource.tags has department) ||
            (principal.allowedTagsForRole has "Role-B" && principal.allowedTagsForRole["Role-B"] has department && resource.tags has department &&
                (principal.allowedTagsForRole["Role-B"].department.contains("ALL") || resource.tags.department.contains("ALL") || principal.allowedTagsForRole["Role-B"].department.containsAll(resource.tags.department)))
        )
    )
};