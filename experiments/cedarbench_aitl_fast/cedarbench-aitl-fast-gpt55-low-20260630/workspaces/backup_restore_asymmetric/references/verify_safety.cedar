permit (principal is Operator, action == Action::"verify", resource is System)
when { principal.role == "engineer" || principal.role == "sre" || principal.role == "admin" };
