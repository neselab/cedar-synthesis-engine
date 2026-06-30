// Floor: any user MUST be permitted to `prepare` any document. The
// first step has no preconditions.
permit (
    principal is User,
    action == Action::"prepare",
    resource is Document
);
