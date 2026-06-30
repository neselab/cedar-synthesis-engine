permit (principal is User, action == Action::"reject", resource is Document)
when { principal.role == "approver" };
