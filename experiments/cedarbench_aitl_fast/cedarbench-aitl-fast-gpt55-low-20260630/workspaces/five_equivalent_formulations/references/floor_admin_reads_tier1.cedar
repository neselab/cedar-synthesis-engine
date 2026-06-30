// FLOOR: An admin User MUST be permitted to read a tier-1 Doc.
// Tests the overlap corner where BOTH branches of the disjunction
// hold. This is implied by either of the other two floors but is
// worth pinning explicitly so a candidate that botches both branches
// (e.g. accidentally encoded XOR) is caught here as well.
permit (
    principal,
    action == Action::"read",
    resource
)
when {
    principal.role == "admin" && resource.tier == 1
};
