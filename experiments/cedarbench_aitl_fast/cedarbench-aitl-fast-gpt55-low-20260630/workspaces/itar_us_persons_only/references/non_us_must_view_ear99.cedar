// Floor: a NON_US engineer MUST be permitted to view uncontrolled
// (EAR99, non-ITAR) technical data.
permit (
    principal is Engineer,
    action == Action::"view",
    resource is TechnicalData
)
when {
    principal.citizenshipStatus == "NON_US"
    && !resource.itarControlled
    && resource.earCategory == "EAR99"
};
