// Floor: a legal_team user MUST access a record under legal hold.
// Confines to legalHold=true so R1 strictly fires (containsPII may be
// either; we further pin containsPII=false to avoid any ambiguity with
// R2's exclusion logic and to keep the floor inside R1's pure region).
permit (
    principal is User,
    action == Action::"access",
    resource is Record
)
when {
    resource.legalHold
    && !resource.containsPII
    && principal.role == "legal_team"
};
