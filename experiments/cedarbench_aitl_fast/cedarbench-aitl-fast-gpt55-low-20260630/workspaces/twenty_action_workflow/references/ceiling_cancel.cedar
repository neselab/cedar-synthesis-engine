permit (principal is User, action == Action::"cancel", resource is Document)
when { (principal.role == "requester" || principal.role == "manager" || principal.role == "admin") };
