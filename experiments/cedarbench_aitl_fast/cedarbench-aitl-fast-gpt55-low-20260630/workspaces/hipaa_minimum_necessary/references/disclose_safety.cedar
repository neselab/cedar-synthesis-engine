// Ceiling: disclose permitted only when purposeAttested AND disclosureLog
//   attested AND (role-purpose-category matrix satisfied
//   OR patient-authorized override).
permit (
    principal is Workforce,
    action == Action::"disclose",
    resource is PatientRecord
)
when {
    context.purposeAttested
    && context.disclosureLog
    && (
        (
            principal.role == "clinician"
            && context.declaredPurpose == "treatment"
        )
        || (
            principal.role == "billing"
            && context.declaredPurpose == "payment"
            && (resource.dataCategory == "billing" || resource.dataCategory == "demographic")
        )
        || (
            principal.role == "researcher"
            && context.declaredPurpose == "research"
            && resource.dataCategory == "research"
        )
        || (
            principal.role == "privacy_officer"
            && context.declaredPurpose == "operations"
        )
        || (context has patientAuthorized && context.patientAuthorized)
    )
};
