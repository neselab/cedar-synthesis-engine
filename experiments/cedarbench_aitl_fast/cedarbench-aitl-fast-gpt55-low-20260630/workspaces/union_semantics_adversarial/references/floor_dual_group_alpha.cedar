// Floor: a user in BOTH groupA and groupB MUST still be permitted to
// access alpha resources (their groupA membership applies). This floor
// exists to ensure the candidate doesn't accidentally encode mutual
// exclusion (e.g., "groupA XOR groupB") when fixing the union trap.
permit (principal is User, action == Action::"access", resource is Resource)
when {
    principal.groupA && principal.groupB && resource.category == "alpha"
};
