permit (
  principal is User,
  action in Action::"Role-A Actions",
  resource is Workspace
)
when {
  principal in Role::"Role-A" &&
  principal.allowedTagsForRole has "Role-A" &&

  (
    !(principal.allowedTagsForRole["Role-A"] has production_status && resource.tags has production_status) ||
    (
      principal.allowedTagsForRole["Role-A"] has production_status &&
      resource.tags has production_status &&
      (
        principal.allowedTagsForRole["Role-A"].production_status.contains("ALL") ||
        resource.tags.production_status.contains("ALL") ||
        principal.allowedTagsForRole["Role-A"].production_status.containsAll(resource.tags.production_status)
      )
    )
  ) &&

  (
    !(principal.allowedTagsForRole["Role-A"] has country && resource.tags has country) ||
    (
      principal.allowedTagsForRole["Role-A"] has country &&
      resource.tags has country &&
      (
        principal.allowedTagsForRole["Role-A"].country.contains("ALL") ||
        resource.tags.country.contains("ALL") ||
        principal.allowedTagsForRole["Role-A"].country.containsAll(resource.tags.country)
      )
    )
  ) &&

  (
    !(principal.allowedTagsForRole["Role-A"] has stage && resource.tags has stage) ||
    (
      principal.allowedTagsForRole["Role-A"] has stage &&
      resource.tags has stage &&
      (
        principal.allowedTagsForRole["Role-A"].stage.contains("ALL") ||
        resource.tags.stage.contains("ALL") ||
        principal.allowedTagsForRole["Role-A"].stage.containsAll(resource.tags.stage)
      )
    )
  )
};

permit (
  principal is User,
  action == Action::"ReadWorkspace",
  resource is Workspace
)
when {
  principal in Role::"Role-B" &&
  principal.allowedTagsForRole has "Role-B" &&

  (
    !(principal.allowedTagsForRole["Role-B"] has production_status && resource.tags has production_status) ||
    (
      principal.allowedTagsForRole["Role-B"] has production_status &&
      resource.tags has production_status &&
      (
        principal.allowedTagsForRole["Role-B"].production_status.contains("ALL") ||
        resource.tags.production_status.contains("ALL") ||
        principal.allowedTagsForRole["Role-B"].production_status.containsAll(resource.tags.production_status)
      )
    )
  ) &&

  (
    !(principal.allowedTagsForRole["Role-B"] has country && resource.tags has country) ||
    (
      principal.allowedTagsForRole["Role-B"] has country &&
      resource.tags has country &&
      (
        principal.allowedTagsForRole["Role-B"].country.contains("ALL") ||
        resource.tags.country.contains("ALL") ||
        principal.allowedTagsForRole["Role-B"].country.containsAll(resource.tags.country)
      )
    )
  ) &&

  (
    !(principal.allowedTagsForRole["Role-B"] has stage && resource.tags has stage) ||
    (
      principal.allowedTagsForRole["Role-B"] has stage &&
      resource.tags has stage &&
      (
        principal.allowedTagsForRole["Role-B"].stage.contains("ALL") ||
        resource.tags.stage.contains("ALL") ||
        principal.allowedTagsForRole["Role-B"].stage.containsAll(resource.tags.stage)
      )
    )
  )
};

permit (
  principal is User,
  action == Action::"ReadWorkspace",
  resource is Workspace
)
when {
  principal == resource.owner
};

forbid (
  principal is User,
  action in Action::"Role-A Actions",
  resource is Workspace
)
when {
  principal in Role::"Role-A" &&
  resource.sensitivity > 3
}
unless {
  action == Action::"ReadWorkspace" &&
  principal == resource.owner
};

forbid (
  principal is User,
  action == Action::"ReadWorkspace",
  resource is Workspace
)
when {
  principal in Role::"Role-B" &&
  resource.sensitivity > 1
}
unless {
  principal == resource.owner ||
  (
    principal in Role::"Role-A" &&
    resource.sensitivity <= 3 &&
    principal.allowedTagsForRole has "Role-A" &&

    (
      !(principal.allowedTagsForRole["Role-A"] has production_status && resource.tags has production_status) ||
      (
        principal.allowedTagsForRole["Role-A"] has production_status &&
        resource.tags has production_status &&
        (
          principal.allowedTagsForRole["Role-A"].production_status.contains("ALL") ||
          resource.tags.production_status.contains("ALL") ||
          principal.allowedTagsForRole["Role-A"].production_status.containsAll(resource.tags.production_status)
        )
      )
    ) &&

    (
      !(principal.allowedTagsForRole["Role-A"] has country && resource.tags has country) ||
      (
        principal.allowedTagsForRole["Role-A"] has country &&
        resource.tags has country &&
        (
          principal.allowedTagsForRole["Role-A"].country.contains("ALL") ||
          resource.tags.country.contains("ALL") ||
          principal.allowedTagsForRole["Role-A"].country.containsAll(resource.tags.country)
        )
      )
    ) &&

    (
      !(principal.allowedTagsForRole["Role-A"] has stage && resource.tags has stage) ||
      (
        principal.allowedTagsForRole["Role-A"] has stage &&
        resource.tags has stage &&
        (
          principal.allowedTagsForRole["Role-A"].stage.contains("ALL") ||
          resource.tags.stage.contains("ALL") ||
          principal.allowedTagsForRole["Role-A"].stage.containsAll(resource.tags.stage)
        )
      )
    )
  )
};

forbid (
  principal is User,
  action,
  resource is Workspace
)
when {
  (action == Action::"UpdateWorkspace" || action == Action::"DeleteWorkspace") &&
  resource.isApproved == false
};