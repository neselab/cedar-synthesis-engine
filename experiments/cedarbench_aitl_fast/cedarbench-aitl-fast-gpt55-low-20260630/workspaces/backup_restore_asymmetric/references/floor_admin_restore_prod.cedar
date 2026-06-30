permit (principal is Operator, action == Action::"restore", resource is System)
when { principal.role == "admin" && resource.environment == "production" };
