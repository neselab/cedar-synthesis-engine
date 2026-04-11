// Ceiling: editRecord is permitted only when the clinician is at the
// same hospital AND the patient is on the clinician's care team.
// Break-glass is NOT authorized for edits — this is the policy's
// crucial safety property (an on-call clinician in an emergency can
// VIEW another patient's record, but they cannot MODIFY it).
permit (
    principal is Clinician,
    action == Action::"editRecord",
    resource is Record
)
when {
    principal.hospital == resource.hospital
    && resource.patient in principal.careTeamPatients
};
