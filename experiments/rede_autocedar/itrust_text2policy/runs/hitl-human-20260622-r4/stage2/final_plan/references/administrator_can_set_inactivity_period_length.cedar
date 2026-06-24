permit (principal, action == Action::"setInactivityPeriodLength", resource) when {
    (context.session.isActive)
    && !(!context.session.isActive)
};