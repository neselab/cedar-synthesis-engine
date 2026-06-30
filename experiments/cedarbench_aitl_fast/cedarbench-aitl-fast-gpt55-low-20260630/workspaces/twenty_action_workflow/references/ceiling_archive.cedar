permit (principal is User, action == Action::"archive", resource is Document)
when { (principal.role == "manager" || principal.role == "admin") };
