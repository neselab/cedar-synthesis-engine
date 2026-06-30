permit (
    principal is User,
    action == Action::"fork",
    resource is Repository
)
when { principal in resource.readers };