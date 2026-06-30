permit (
    principal is User,
    action == Action::"add_admin",
    resource is Repository
)
when { principal in resource.admins && !resource.isArchived };