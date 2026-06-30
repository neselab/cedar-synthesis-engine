permit (principal is User, action == Action::"viewPII", resource is Order)
when { principal.role == "role_06" };
