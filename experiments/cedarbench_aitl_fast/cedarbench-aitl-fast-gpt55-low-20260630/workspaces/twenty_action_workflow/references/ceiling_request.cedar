permit (principal is User, action == Action::"request", resource is Document)
when { (principal.role == "requester" || principal.role == "manager" || principal.role == "admin") };
