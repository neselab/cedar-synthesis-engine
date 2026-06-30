permit (principal is User, action == Action::"shipOrder", resource is Order)
when { principal.role == "role_09" };
