permit (principal, action == Action::"createLhcp", resource) when {
    (context.session.isActive)
    && !(!context.session.isActive)
};