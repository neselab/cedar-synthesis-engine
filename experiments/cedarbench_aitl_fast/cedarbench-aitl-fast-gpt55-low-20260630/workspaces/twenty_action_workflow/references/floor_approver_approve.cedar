permit (principal is User, action == Action::"approve", resource is Document)
when { principal.role == "approver" };
