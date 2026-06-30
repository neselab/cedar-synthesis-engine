// Floor: a junior active employee (seniority < 5, no MGMT-101 cert)
// MUST still be permitted to view. View is gated only on
// employmentStatus — seniority and certifications are irrelevant
// for view. Catches the failure mode where the synthesizer over-
// gates view on the manager predicate.
permit (
    principal is Employee,
    action == Action::"view",
    resource is Resource
)
when {
    principal.employmentStatus == "active"
    && principal.seniority < 5
    && !(principal.certifications.contains("MGMT-101"))
};
