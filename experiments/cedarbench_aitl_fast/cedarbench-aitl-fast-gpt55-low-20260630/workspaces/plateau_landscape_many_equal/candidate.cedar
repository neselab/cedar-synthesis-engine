permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    (principal.bool1 && principal.bool2 && principal.bool3 && !principal.bool4 && !principal.bool5) ||
    (principal.bool1 && principal.bool2 && !principal.bool3 && principal.bool4 && !principal.bool5) ||
    (principal.bool1 && principal.bool2 && !principal.bool3 && !principal.bool4 && principal.bool5) ||
    (principal.bool1 && !principal.bool2 && principal.bool3 && principal.bool4 && !principal.bool5) ||
    (principal.bool1 && !principal.bool2 && principal.bool3 && !principal.bool4 && principal.bool5) ||
    (principal.bool1 && !principal.bool2 && !principal.bool3 && principal.bool4 && principal.bool5) ||
    (!principal.bool1 && principal.bool2 && principal.bool3 && principal.bool4 && !principal.bool5) ||
    (!principal.bool1 && principal.bool2 && principal.bool3 && !principal.bool4 && principal.bool5) ||
    (!principal.bool1 && principal.bool2 && !principal.bool3 && principal.bool4 && principal.bool5) ||
    (!principal.bool1 && !principal.bool2 && principal.bool3 && principal.bool4 && principal.bool5)
};