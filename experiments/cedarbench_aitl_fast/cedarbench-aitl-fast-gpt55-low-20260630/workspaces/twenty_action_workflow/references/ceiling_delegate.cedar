permit (principal is User, action == Action::"delegate", resource is Document)
when { (principal.role == "approver" || principal.role == "manager" || principal.role == "admin") };
