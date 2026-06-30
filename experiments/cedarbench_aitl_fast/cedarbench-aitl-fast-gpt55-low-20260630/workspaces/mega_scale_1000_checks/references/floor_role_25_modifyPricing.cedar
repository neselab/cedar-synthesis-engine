permit (principal is User, action == Action::"modifyPricing", resource is Order)
when { principal.role == "role_25" };
