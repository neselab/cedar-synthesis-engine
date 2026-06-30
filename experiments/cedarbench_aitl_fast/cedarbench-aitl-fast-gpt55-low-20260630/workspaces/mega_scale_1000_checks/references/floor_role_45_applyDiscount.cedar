permit (principal is User, action == Action::"applyDiscount", resource is Order)
when { principal.role == "role_45" };
