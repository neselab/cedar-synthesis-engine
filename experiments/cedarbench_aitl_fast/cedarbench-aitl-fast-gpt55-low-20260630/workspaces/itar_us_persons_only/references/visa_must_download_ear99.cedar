// Floor: a VISA-status engineer MUST be permitted to download EAR99
// (uncontrolled, non-ITAR) data — no location restriction since the
// data is uncontrolled.
permit (
    principal is Engineer,
    action == Action::"download",
    resource is TechnicalData
)
when {
    principal.citizenshipStatus == "VISA"
    && !resource.itarControlled
    && resource.earCategory == "EAR99"
};
