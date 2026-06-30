permit (principal is Operator, action == Action::"backup", resource is System)
when { principal.role == "engineer" || principal.role == "sre" || principal.role == "admin" };
