permit (principal is User, action == Action::"sign", resource is Document)
when { (principal.role == "approver" || principal.role == "manager" || principal.role == "admin") };
