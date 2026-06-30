permit (principal is User, action == Action::"review", resource is Document)
when { principal.role == "reviewer" };
