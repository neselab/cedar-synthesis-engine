permit (principal is Operator, action == Action::"restore", resource is System)
when { principal.role == "sre" && principal.isOnCall && resource.environment == "production" };
