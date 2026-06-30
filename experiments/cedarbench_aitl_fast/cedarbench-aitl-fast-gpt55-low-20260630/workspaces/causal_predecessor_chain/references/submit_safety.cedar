// Ceiling for `submit`: only permitted when the host has attached a
// predecessor attestation AND the attested action was "prepare".
// `has`-guarded per §8.3.
permit (
    principal is User,
    action == Action::"submit",
    resource is Document
)
when {
    context has predecessorAuthorized
    && context.predecessorAuthorized.actionType == "prepare"
};
