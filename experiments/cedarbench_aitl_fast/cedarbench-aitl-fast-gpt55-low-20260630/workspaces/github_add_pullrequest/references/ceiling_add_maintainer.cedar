permit (
    principal is User,
    action == Action::"add_maintainer",
    resource is Repository
)
when { principal in resource.admins && !resource.isArchived };