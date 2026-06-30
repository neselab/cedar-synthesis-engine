permit (
  principal is User,
  action in Action::"Role-A Actions",
  resource is Workspace
)
when {
  principal in Role::"Role-A" &&
  (
    if principal.allowedTagsForRole has "Role-A" then
      (
        if principal.allowedTagsForRole["Role-A"] has production_status then
          (
            if resource.tags has production_status then
              principal.allowedTagsForRole["Role-A"].production_status.containsAll(resource.tags.production_status)
              principal.allowedTagsForRole["Role-A"].country.containsAll(resource.tags.country)
              principal.allowedTagsForRole["Role-A"].stage.containsAll(resource.tags.stage)
};

permit (
  principal is User,
  action in Action::"Role-B Actions",
  resource is Workspace
)
when {
  principal in Role::"Role-B" &&
  (
    if principal.allowedTagsForRole has "Role-B" then
      (
        if principal.allowedTagsForRole["Role-B"] has production_status then
          (
            if resource.tags has production_status then
              principal.allowedTagsForRole["Role-B"].production_status.containsAll(resource.tags.production_status)
              principal.allowedTagsForRole["Role-B"].country.containsAll(resource.tags.country)
              principal.allowedTagsForRole["Role-B"].stage.containsAll(resource.tags.stage)
};