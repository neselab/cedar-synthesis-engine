// Floor: a same-hospital care-team member MUST be permitted to viewRecord,
// regardless of emergency status. This is the baseline care-team access.
permit (
    principal is Clinician,
    action == Action::"viewRecord",
    resource is Record
)
when {
    principal.hospital == resource.hospital
    && resource.patient in principal.careTeamPatients
};
