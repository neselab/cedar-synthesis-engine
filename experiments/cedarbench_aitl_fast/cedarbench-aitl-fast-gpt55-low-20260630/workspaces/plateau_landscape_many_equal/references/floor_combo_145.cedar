// Floor: a User with (bool1, bool4, bool5) = (true, true, true) and
// (bool2, bool3) = (false, false) MUST be permitted. Pins disjunct 6
// of the 10-disjunct exactly-3-of-5 enumeration.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.bool1
    && !principal.bool2
    && !principal.bool3
    && principal.bool4
    && principal.bool5
};
