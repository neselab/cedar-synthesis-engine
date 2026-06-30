permit (principal is User, action == Action::"comment", resource is Document)
when { principal.role != "" };
