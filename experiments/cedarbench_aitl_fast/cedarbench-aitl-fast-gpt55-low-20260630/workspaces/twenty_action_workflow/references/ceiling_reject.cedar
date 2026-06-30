permit (principal is User, action == Action::"reject", resource is Document)
when { (principal.role == "approver" || principal.role == "manager" || principal.role == "admin") };
