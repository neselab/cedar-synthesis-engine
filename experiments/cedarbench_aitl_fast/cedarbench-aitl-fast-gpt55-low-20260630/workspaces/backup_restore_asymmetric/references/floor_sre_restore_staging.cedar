permit (principal is Operator, action == Action::"restore", resource is System)
when { principal.role == "sre" && resource.environment == "staging" };
