permit (principal, action == Action::"createEmergencyResponder", resource) when {
    (context.session.isActive)
    && !(!context.session.isActive)
};