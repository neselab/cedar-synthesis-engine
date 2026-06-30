permit (principal is User, action == Action::"resubmit", resource is Document)
when { (principal.role == "requester" || principal.role == "manager") };
