// Floor: collecting anonymous data MUST be permitted regardless of
// the user's age or whether parental consent has been obtained.
// Anonymous data carries no PII so COPPA does not apply.
permit (
    principal is User,
    action == Action::"collect",
    resource is DataPoint
)
when {
    resource.category == "anonymous"
};
