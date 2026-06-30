permit (
    principal is User,
    action == Action::"prepare",
    resource is Document
);

permit (
    principal is User,
    action == Action::"submit",
    resource is Document
)
when {
    context has predecessorAuthorized &&
    context.predecessorAuthorized.actionType == "prepare"
};

permit (
    principal is User,
    action == Action::"approve",
    resource is Document
)
when {
    context has predecessorAuthorized &&
    context.predecessorAuthorized.actionType == "submit" &&
    context.predecessorAuthorized.actor != principal
};