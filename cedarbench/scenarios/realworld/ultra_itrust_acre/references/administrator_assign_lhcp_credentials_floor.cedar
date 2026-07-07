permit (principal, action == Action::"assignCredentials", resource) when { context.session.isActive && context.session has administratorUser && context.session.administratorUser == principal };
