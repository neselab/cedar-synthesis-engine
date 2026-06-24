permit (principal, action == Action::"createUap", resource) when {
    (context.session.isActive)
    && !(!context.session.isActive)
};