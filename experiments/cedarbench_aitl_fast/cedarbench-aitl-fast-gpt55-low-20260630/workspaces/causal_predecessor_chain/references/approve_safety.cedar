// Ceiling for `approve`: only permitted when the host has attached a
// predecessor attestation AND the attested action was "submit" AND
// the submitter is NOT the user now trying to approve (separation of
// duties). `has`-guarded per §8.3.
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
