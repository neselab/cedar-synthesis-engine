permit (principal is User, action == Action::"deleteMessage", resource is Channel)
when { principal == resource.owner || resource.moderators.contains(principal) };
