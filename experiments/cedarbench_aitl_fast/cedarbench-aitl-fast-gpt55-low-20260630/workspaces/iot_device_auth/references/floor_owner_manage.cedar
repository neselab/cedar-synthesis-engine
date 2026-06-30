permit (principal is User, action == Action::"manage", resource is Endpoint)
when { principal == resource.owner };
