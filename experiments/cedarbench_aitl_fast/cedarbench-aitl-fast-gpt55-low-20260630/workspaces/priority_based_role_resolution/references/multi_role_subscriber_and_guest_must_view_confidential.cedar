// Floor (PRIORITY TEST): a User holding BOTH "subscriber" and "guest"
// MUST be permitted to viewRecord on a "confidential" Record.
//
// This is the role-intersection trap (harness_fix_log.md §8.6). The
// subscriber permit must fire even though the user also holds the
// guest role. A candidate that encodes priority via a forbid like
//   `forbid when principal.roles.contains("guest") && tier == "confidential"`
// would FAIL this floor.
permit (
    principal is User,
    action == Action::"viewRecord",
    resource is Record
)
when {
    principal.roles.contains("subscriber")
    && principal.roles.contains("guest")
    && resource.tier == "confidential"
};
