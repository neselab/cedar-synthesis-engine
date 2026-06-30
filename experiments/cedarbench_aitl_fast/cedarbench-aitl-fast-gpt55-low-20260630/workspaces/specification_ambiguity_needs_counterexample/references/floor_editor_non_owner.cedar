// Floor A: an editor who is NOT the document owner MUST be permitted to edit.
// This is the discriminating counterexample that rules out the
// over-restrictive "editor AND owner" reading.
permit (
    principal is User,
    action == Action::"edit",
    resource is Document
)
when {
    principal.role == "editor"
    && principal != resource.owner
};
