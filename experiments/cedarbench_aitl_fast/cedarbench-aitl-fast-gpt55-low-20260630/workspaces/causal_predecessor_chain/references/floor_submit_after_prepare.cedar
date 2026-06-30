// Floor: a user MUST be permitted to `submit` whenever the host has
// attested that the immediate predecessor was a successful "prepare".
permit (
    principal is User,
    action == Action::"submit",
    resource is Document
)
when {
    context has predecessorAuthorized
    && context.predecessorAuthorized.actionType == "prepare"
};
