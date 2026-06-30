permit (principal is User, action == Action::"maskPII", resource is Order)
when { principal.role == "role_31" };
