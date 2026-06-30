permit (principal is User, action == Action::"close", resource is Document)
when { principal.role == "manager" };
