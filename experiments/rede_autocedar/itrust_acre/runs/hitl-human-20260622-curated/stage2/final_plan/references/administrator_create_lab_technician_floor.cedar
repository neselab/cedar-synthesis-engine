permit (principal, action == Action::"createLabTechnician", resource) when { context.session.isActive && context.session has administratorUser && context.session.administratorUser == principal };
