permit (principal is User, action == Action::"export", resource is Document)
when { principal.role == "auditor" };
