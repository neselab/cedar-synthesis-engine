// Ceiling: viewRecord is permitted only when the clinician is at the
// same hospital as the record AND (the patient is on the clinician's
// care team OR the break-glass conditions hold).
permit (
    principal is Clinician,
    action == Action::"viewRecord",
    resource is Record
)
when {
    principal.hospital == resource.hospital
    && (
        resource.patient in principal.careTeamPatients
        || (
            principal.isOnCall
            && context.emergencyActive
            && context.emergencyReason != ""
        )
    )
};
