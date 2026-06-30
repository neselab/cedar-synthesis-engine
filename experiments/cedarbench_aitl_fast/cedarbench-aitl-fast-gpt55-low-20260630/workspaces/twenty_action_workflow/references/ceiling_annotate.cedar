permit (principal is User, action == Action::"annotate", resource is Document)
when { (principal.role == "requester" || principal.role == "reviewer" || principal.role == "approver" || principal.role == "manager" || principal.role == "auditor") };
