permit (principal, action == Action::"editPatientData", resource) when {
    (principal is HCP && resource is Patient && !(context.editedField == "mid"))
    && !(context.editedField == "mid")
};