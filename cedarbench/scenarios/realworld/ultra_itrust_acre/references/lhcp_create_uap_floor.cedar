permit (principal, action == Action::"createUAP", resource) when { context.session.isActive && context.session has lhcpUser && context.session.lhcpUser == principal };
