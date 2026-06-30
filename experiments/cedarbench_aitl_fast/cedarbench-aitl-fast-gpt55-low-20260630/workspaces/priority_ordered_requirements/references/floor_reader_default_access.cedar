// Floor: a user with role "reader" MUST access a record that is
// neither under legal hold nor contains PII (R3 default fires).
permit (
    principal is User,
    action == Action::"access",
    resource is Record
)
when {
    !resource.legalHold
    && !resource.containsPII
    && principal.role == "reader"
};
