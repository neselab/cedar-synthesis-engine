permit (principal, action == Action::"disablePatient", resource) when { context.session.isActive && context.session has hcpUser && context.session.hcpUser == principal };
