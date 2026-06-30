permit (
    principal is User,
    action == Action::"Edit",
    resource is Document
)
when {
    context.hasPatientConsent == true
};