permit (principal is User, action == Action::"audit", resource is Document)
when { (principal.role == "auditor" || principal.role == "admin") };
