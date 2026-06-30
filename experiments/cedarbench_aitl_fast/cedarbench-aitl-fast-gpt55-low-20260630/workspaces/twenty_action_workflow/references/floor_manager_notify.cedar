permit (principal is User, action == Action::"notify", resource is Document)
when { principal.role == "manager" };
