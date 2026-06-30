// Floor: an on-call clinician at the same hospital with an active
// emergency and a non-empty attested reason MUST be permitted to
// viewRecord for a non-care-team patient. This is the break-glass path.
//
// The `!(resource.patient in principal.careTeamPatients)` clause
// narrows the floor to the break-glass case specifically (the
// care-team path is covered by the other view floor). This makes it
// easier to test the break-glass path in isolation.
permit (
    principal is Clinician,
    action == Action::"viewRecord",
    resource is Record
)
when {
    principal.hospital == resource.hospital
    && !(resource.patient in principal.careTeamPatients)
    && principal.isOnCall
    && context.emergencyActive
    && context.emergencyReason != ""
};
