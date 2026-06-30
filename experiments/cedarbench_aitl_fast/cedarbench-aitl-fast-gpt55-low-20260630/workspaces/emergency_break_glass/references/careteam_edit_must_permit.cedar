// Floor: a same-hospital care-team member MUST be permitted to editRecord.
// This is the baseline care-team edit access.
permit (
    principal is Clinician,
    action == Action::"editRecord",
    resource is Record
)
when {
    principal.hospital == resource.hospital
    && resource.patient in principal.careTeamPatients
};
