// Ceiling: view permitted only when purposeAttested AND
//   (role-purpose-category matrix satisfied
//    OR patient-authorized override).
permit (
    principal is Workforce,
    action == Action::"view",
    resource is PatientRecord
)
when {
    context.purposeAttested
    && (
        // Role-purpose-category matrix
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
        // Patient-authorization override (waives matrix, not attestation)
        || (context has patientAuthorized && context.patientAuthorized)
    )
};
