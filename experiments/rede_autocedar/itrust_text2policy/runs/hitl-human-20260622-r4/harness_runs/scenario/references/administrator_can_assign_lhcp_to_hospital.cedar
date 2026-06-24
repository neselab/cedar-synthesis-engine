permit (principal, action == Action::"assignLhcpToHospital", resource) when {
    (context.session.isActive)
    && !(!context.session.isActive)
};