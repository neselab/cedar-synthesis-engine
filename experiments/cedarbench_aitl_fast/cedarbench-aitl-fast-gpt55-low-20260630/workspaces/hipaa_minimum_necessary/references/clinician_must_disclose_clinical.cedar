// Floor: a clinician with attested treatment purpose AND audit-log
// attestation MUST be permitted to disclose a clinical PatientRecord.
permit (
    principal is Workforce,
    action == Action::"disclose",
    resource is PatientRecord
)
when {
    principal.role == "clinician"
    && context.purposeAttested
    && context.declaredPurpose == "treatment"
    && context.disclosureLog
    && resource.dataCategory == "clinical"
};
