permit (principal, action == Action::"editPatient", resource) when { context.session.isActive && context.session has hcpUser && context.session.hcpUser == principal && resource.isActive };
