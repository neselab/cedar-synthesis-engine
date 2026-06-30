permit (principal is User, action == Action::"post", resource is Channel)
when { resource.members.contains(principal) && !resource.isArchived };
