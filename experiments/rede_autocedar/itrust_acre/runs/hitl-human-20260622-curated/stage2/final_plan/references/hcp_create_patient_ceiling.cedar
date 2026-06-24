permit (principal, action == Action::"createPatient", resource) when { context.session.isActive && context.session has hcpUser && context.session.hcpUser == principal };
