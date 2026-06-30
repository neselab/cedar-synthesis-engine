// Floor: a US citizen with clearanceVerified, accessing from the US,
// MUST be permitted to export technical data.
permit (
    principal is Engineer,
    action == Action::"export",
    resource is TechnicalData
)
when {
    principal.citizenshipStatus == "US_CITIZEN"
    && principal.clearanceVerified
    && context.accessLocation == "US"
};
