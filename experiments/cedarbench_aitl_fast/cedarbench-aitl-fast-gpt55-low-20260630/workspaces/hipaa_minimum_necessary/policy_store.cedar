// Policy store — verified policies appended here

// --- Verified (eval iteration 2) ---
permit (
    principal is Workforce,
    action == Action::"view",
    resource is PatientRecord
)
when {
    context.purposeAttested == true
    &&
    (
        (
            principal.role == "clinician"
            && context.declaredPurpose == "treatment"
        )
        ||
        (
            principal.role == "billing"
            && context.declaredPurpose == "payment"
            && (resource.dataCategory == "billing" || resource.dataCategory == "demographic")
        )
        ||
        (
            principal.role == "researcher"
            && context.declaredPurpose == "research"
            && resource.dataCategory == "research"
        )
        ||
        (
            principal.role == "privacy_officer"
            && context.declaredPurpose == "operations"
        )
        ||
        (
            context has patientAuthorized
            && context.patientAuthorized == true
        )
    )
};

permit (
    principal is Workforce,
    action == Action::"disclose",
    resource is PatientRecord
)
when {
    context.purposeAttested == true
    && context.disclosureLog == true
    &&
    (
        (
            principal.role == "clinician"
            && context.declaredPurpose == "treatment"
        )
        ||
        (
            principal.role == "billing"
            && context.declaredPurpose == "payment"
            && (resource.dataCategory == "billing" || resource.dataCategory == "demographic")
        )
        ||
        (
            principal.role == "researcher"
            && context.declaredPurpose == "research"
            && resource.dataCategory == "research"
        )
        ||
        (
            principal.role == "privacy_officer"
            && context.declaredPurpose == "operations"
        )
        ||
        (
            context has patientAuthorized
            && context.patientAuthorized == true
        )
    )
};

permit (
    principal is Workforce,
    action == Action::"amend",
    resource is PatientRecord
)
when {
    principal.role == "clinician"
    && context.declaredPurpose == "treatment"
    && context.purposeAttested == true
    && resource.dataCategory == "clinical"
};
