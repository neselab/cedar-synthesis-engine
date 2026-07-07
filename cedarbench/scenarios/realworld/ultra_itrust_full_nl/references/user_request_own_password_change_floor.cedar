permit (principal is User, action == Action::"requestPasswordChange", resource is User) when {
    (context.session.isActive && context.session has user && context.session has user && context.session has user && context.session has user && context.session has user && context.session has user && context.session.user == principal && resource == principal)
    && !(resource is Patient && resource.isDeactivated)
};