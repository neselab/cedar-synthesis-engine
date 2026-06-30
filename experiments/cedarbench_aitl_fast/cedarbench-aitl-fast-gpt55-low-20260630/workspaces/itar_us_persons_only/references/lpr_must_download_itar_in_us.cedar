// Floor: an LPR engineer accessing from the US MUST be permitted to
// download ITAR-controlled data.
permit (
    principal is Engineer,
    action == Action::"download",
    resource is TechnicalData
)
when {
    principal.citizenshipStatus == "LPR"
    && resource.itarControlled
    && context.accessLocation == "US"
};
