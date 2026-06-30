permit (principal is User, action == Action::"cc", resource is Document)
when { principal.role == "requester" };
