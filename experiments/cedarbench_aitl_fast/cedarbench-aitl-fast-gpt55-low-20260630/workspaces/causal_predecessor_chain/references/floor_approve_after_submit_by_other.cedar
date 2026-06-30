// Floor: a user MUST be permitted to `approve` whenever the host has
// attested that the immediate predecessor was a successful "submit"
// by a DIFFERENT user (separation of duties satisfied).
permit (
    principal is User,
    action == Action::"approve",
    resource is Document
)
when {
    context has predecessorAuthorized
    && context.predecessorAuthorized.actionType == "submit"
    && context.predecessorAuthorized.actor != principal
};
