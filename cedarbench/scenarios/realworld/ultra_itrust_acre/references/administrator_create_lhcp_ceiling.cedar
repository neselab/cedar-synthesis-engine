permit (principal, action == Action::"createLHCP", resource) when { context.session.isActive && context.session has administratorUser && context.session.administratorUser == principal };
