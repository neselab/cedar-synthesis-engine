permit (principal is User, action == Action::"countersign", resource is Document)
when { (principal.role == "manager" || principal.role == "admin") };
