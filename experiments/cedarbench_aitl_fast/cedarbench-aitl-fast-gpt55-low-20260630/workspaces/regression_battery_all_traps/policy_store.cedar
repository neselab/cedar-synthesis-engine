// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
forbid (principal is User, action, resource is Document)
when {
    principal.isBlocked
};

permit (principal is User, action == Action::"read", resource is Document)
when {
    context.now < resource.expiresAt.offset(context.graceWindow) &&
    (
        (
            resource.classification == "public" &&
            (
                principal.primaryRole == "admin" ||
                principal.secondaryRoles.contains("admin") ||
                principal.primaryRole == "manager" ||
                principal.secondaryRoles.contains("manager") ||
                principal.primaryRole == "contractor" ||
                principal.secondaryRoles.contains("contractor")
            )
        ) ||
        (
            resource.classification == "confidential" &&
            (
                principal.primaryRole == "admin" ||
                principal.secondaryRoles.contains("admin") ||
                principal.primaryRole == "manager" ||
                principal.secondaryRoles.contains("manager") ||
                (
                    (
                        principal.primaryRole == "contractor" ||
                        principal.secondaryRoles.contains("contractor")
                    ) &&
                    context has mfaToken &&
                    context.mfaToken != ""
                )
            )
        )
    )
};

permit (principal is User, action == Action::"edit", resource is Document)
when {
    context.now < resource.expiresAt.offset(context.graceWindow) &&
    (
        principal.primaryRole == "admin" ||
        principal.secondaryRoles.contains("admin") ||
        principal.primaryRole == "manager" ||
        principal.secondaryRoles.contains("manager")
    )
};

permit (principal is User, action == Action::"archive", resource is Document)
when {
    context.now > resource.expiresAt &&
    (
        principal.primaryRole == "admin" ||
        principal.secondaryRoles.contains("admin")
    )
};
