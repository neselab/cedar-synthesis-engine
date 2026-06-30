permit (principal is User, action == Action::"sign", resource is Document)
when { principal.role == "approver" };
