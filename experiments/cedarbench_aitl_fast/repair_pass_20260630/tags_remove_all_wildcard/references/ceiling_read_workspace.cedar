permit (
    principal is User,
    action,
    resource is Workspace
)
when {
    (
        principal in Role::"Role-A" &&
        (!(principal.allowedTagsForRole has "Role-A") ||
         (principal.allowedTagsForRole has "Role-A" &&
          (!(principal.allowedTagsForRole["Role-A"] has production_status) ||
           (principal.allowedTagsForRole["Role-A"] has production_status &&
            (!(resource.tags has production_status) ||
             (resource.tags has production_status &&
              principal.allowedTagsForRole["Role-A"].production_status.containsAll(resource.tags.production_status))))))) &&
        (!(principal.allowedTagsForRole has "Role-A") ||
         (principal.allowedTagsForRole has "Role-A" &&
          (!(principal.allowedTagsForRole["Role-A"] has country) ||
           (principal.allowedTagsForRole["Role-A"] has country &&
            (!(resource.tags has country) ||
             (resource.tags has country &&
              principal.allowedTagsForRole["Role-A"].country.containsAll(resource.tags.country))))))) &&
        (!(principal.allowedTagsForRole has "Role-A") ||
         (principal.allowedTagsForRole has "Role-A" &&
          (!(principal.allowedTagsForRole["Role-A"] has stage) ||
           (principal.allowedTagsForRole["Role-A"] has stage &&
            (!(resource.tags has stage) ||
             (resource.tags has stage &&
              principal.allowedTagsForRole["Role-A"].stage.containsAll(resource.tags.stage)))))))
    ) ||
    (
        principal in Role::"Role-B" &&
        (!(principal.allowedTagsForRole has "Role-B") ||
         (principal.allowedTagsForRole has "Role-B" &&
          (!(principal.allowedTagsForRole["Role-B"] has production_status) ||
           (principal.allowedTagsForRole["Role-B"] has production_status &&
            (!(resource.tags has production_status) ||
             (resource.tags has production_status &&
              principal.allowedTagsForRole["Role-B"].production_status.containsAll(resource.tags.production_status))))))) &&
        (!(principal.allowedTagsForRole has "Role-B") ||
         (principal.allowedTagsForRole has "Role-B" &&
          (!(principal.allowedTagsForRole["Role-B"] has country) ||
           (principal.allowedTagsForRole["Role-B"] has country &&
            (!(resource.tags has country) ||
             (resource.tags has country &&
              principal.allowedTagsForRole["Role-B"].country.containsAll(resource.tags.country))))))) &&
        (!(principal.allowedTagsForRole has "Role-B") ||
         (principal.allowedTagsForRole has "Role-B" &&
          (!(principal.allowedTagsForRole["Role-B"] has stage) ||
           (principal.allowedTagsForRole["Role-B"] has stage &&
            (!(resource.tags has stage) ||
             (resource.tags has stage &&
              principal.allowedTagsForRole["Role-B"].stage.containsAll(resource.tags.stage)))))))
    )
};