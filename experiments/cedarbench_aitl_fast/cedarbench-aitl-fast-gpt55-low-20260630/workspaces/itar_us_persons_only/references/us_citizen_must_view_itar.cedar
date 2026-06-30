// Floor: a US citizen MUST be permitted to view ITAR-controlled data.
// (No location restriction on view.)
permit (
    principal is Engineer,
    action == Action::"view",
    resource is TechnicalData
)
when {
    principal.citizenshipStatus == "US_CITIZEN"
    && resource.itarControlled
};
