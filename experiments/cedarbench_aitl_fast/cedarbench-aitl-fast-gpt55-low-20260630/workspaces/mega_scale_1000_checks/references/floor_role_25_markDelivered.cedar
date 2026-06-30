permit (principal is User, action == Action::"markDelivered", resource is Order)
when { principal.role == "role_25" };
