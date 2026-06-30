permit (
    principal is User,
    action == Action::"push",
    resource is Repository
)
when { principal in resource.writers && !resource.isArchived };

permit (
    principal is User,
    action == Action::"push",
    resource is Repository
)
when { principal in resource.securityAdmins };
