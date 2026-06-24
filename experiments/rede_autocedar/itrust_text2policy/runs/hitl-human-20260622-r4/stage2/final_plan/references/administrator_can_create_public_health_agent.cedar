permit (principal, action == Action::"createPublicHealthAgent", resource) when {
    (context.session.isActive)
    && !(!context.session.isActive)
};