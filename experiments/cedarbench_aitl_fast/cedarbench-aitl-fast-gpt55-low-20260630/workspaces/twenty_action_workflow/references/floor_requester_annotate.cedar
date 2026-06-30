permit (principal is User, action == Action::"annotate", resource is Document)
when { principal.role == "requester" };
