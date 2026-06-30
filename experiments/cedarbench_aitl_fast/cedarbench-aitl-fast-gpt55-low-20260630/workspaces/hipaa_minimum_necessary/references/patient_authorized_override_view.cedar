// Floor: when the patient has executed a §164.508 authorization
// (context.patientAuthorized == true, has-guarded), any attested
// Workforce member MUST be permitted to view any PatientRecord
// — the authorization waives the minimum-necessary matrix.
permit (
    principal is Workforce,
    action == Action::"view",
    resource is PatientRecord
)
when {
    context.purposeAttested
    && context has patientAuthorized
    && context.patientAuthorized
};
