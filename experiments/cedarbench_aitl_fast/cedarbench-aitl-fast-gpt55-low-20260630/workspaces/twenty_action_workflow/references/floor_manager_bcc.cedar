permit (principal is User, action == Action::"bcc", resource is Document)
when { principal.role == "manager" };
