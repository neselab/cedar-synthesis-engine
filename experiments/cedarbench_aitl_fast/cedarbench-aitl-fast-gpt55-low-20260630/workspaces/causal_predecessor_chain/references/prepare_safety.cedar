// Ceiling for `prepare`: any user may prepare any document. The first
// step in the chain has no predecessor requirement, so the ceiling
// imposes no condition beyond the action / type guards.
permit (
    principal is User,
    action == Action::"prepare",
    resource is Document
);
