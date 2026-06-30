forbid (
    principal is Clinician,
    action in [Action::"viewRecord", Action::"editRecord"],
    resource is Record
)
when {
    principal.hospital != resource.hospital
};

permit (
    principal is Clinician,
    action in [Action::"viewRecord", Action::"editRecord"],
    resource is Record
)
when {
    resource.patient in principal.careTeamPatients
};

permit (
    principal is Clinician,
    action == Action::"viewRecord",
    resource is Record
)
when {
    !(resource.patient in principal.careTeamPatients) &&
    principal.isOnCall == true &&
    context.emergencyActive == true &&
    context.emergencyReason != ""
};