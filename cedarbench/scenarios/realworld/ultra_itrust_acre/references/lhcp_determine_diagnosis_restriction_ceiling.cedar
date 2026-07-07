permit (principal, action == Action::"determineDiagnosisRestrictionAllowed", resource) when { context.session.isActive && context.session has lhcpUser && context.session.lhcpUser == principal };
