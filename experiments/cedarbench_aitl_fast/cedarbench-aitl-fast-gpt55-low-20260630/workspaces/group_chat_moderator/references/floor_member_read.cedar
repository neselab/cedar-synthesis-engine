permit (principal is User, action == Action::"read", resource is Channel)
when { resource.members.contains(principal) && !resource.isArchived };
