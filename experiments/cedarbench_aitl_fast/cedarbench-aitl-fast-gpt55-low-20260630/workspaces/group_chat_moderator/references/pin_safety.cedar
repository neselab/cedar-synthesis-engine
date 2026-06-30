permit (principal is User, action == Action::"pin", resource is Channel)
when { principal == resource.owner || resource.moderators.contains(principal) };
