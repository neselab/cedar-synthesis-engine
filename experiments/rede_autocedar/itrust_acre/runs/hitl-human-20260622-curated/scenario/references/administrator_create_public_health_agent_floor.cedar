permit (principal, action == Action::"createPublicHealthAgent", resource) when { context.session.isActive && context.session has administratorUser && context.session.administratorUser == principal };
