permit (principal is User, action == Action::"reopen", resource is Document)
when { principal.role == "manager" };
