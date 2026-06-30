permit (principal is User, action == Action::"archive", resource is Channel)
when { principal == resource.owner };
