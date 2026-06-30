permit (principal is User, action == Action::"partialRefund", resource is Order)
when { principal.role == "role_40" };
