// Ceiling: access permitted only when EXACTLY 3 of 5 booleans are true.
// Enumerated as the C(5,3) = 10 mutually exclusive 5-tuple cases.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    (principal.bool1 && principal.bool2 && principal.bool3 && !principal.bool4 && !principal.bool5)
    || (principal.bool1 && principal.bool2 && !principal.bool3 && principal.bool4 && !principal.bool5)
    || (principal.bool1 && principal.bool2 && !principal.bool3 && !principal.bool4 && principal.bool5)
    || (principal.bool1 && !principal.bool2 && principal.bool3 && principal.bool4 && !principal.bool5)
    || (principal.bool1 && !principal.bool2 && principal.bool3 && !principal.bool4 && principal.bool5)
    || (principal.bool1 && !principal.bool2 && !principal.bool3 && principal.bool4 && principal.bool5)
    || (!principal.bool1 && principal.bool2 && principal.bool3 && principal.bool4 && !principal.bool5)
    || (!principal.bool1 && principal.bool2 && principal.bool3 && !principal.bool4 && principal.bool5)
    || (!principal.bool1 && principal.bool2 && !principal.bool3 && principal.bool4 && principal.bool5)
    || (!principal.bool1 && !principal.bool2 && principal.bool3 && principal.bool4 && principal.bool5)
};
