permit (principal is User, action == Action::"deleteMessage", resource is Channel)
when { principal == resource.owner };
