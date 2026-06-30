permit (principal is User, action == Action::"cancelOrder", resource is Order)
when { principal.role == "role_06" };
