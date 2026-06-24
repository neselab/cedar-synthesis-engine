permit (principal, action == Action::"viewLhcps", resource) when { context.session.isActive && context.session has patientUser && context.session.patientUser == principal && resource == principal };
