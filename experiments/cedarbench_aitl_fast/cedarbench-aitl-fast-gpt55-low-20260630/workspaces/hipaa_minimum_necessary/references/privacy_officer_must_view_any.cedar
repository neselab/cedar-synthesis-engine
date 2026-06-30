// Floor: a privacy officer with attested operations purpose MUST be
// permitted to view any PatientRecord (oversight access, per §164.530
// compliance-officer responsibilities).
permit (
    principal is Workforce,
    action == Action::"view",
    resource is PatientRecord
)
when {
    principal.role == "privacy_officer"
    && context.purposeAttested
    && context.declaredPurpose == "operations"
};
