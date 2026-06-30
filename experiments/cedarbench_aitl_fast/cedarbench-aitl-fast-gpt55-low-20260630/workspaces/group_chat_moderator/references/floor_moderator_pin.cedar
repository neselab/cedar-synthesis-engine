permit (principal is User, action == Action::"pin", resource is Channel)
when { resource.moderators.contains(principal) };
