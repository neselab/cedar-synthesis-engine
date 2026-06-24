permit (principal, action == Action::"editPatientData", resource) when {
    (context.session.isActive && !(context.fieldName == "mid"))
    && !(context.fieldName == "mid")
    && !(!context.session.isActive)
};