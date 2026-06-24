permit (principal, action == Action::"setInactivityPeriod", resource) when { context.session.isActive && context.session has administratorUser && context.session.administratorUser == principal };
