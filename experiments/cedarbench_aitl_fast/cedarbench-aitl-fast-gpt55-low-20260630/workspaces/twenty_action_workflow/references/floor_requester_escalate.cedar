permit (principal is User, action == Action::"escalate", resource is Document)
when { principal.role == "requester" };
