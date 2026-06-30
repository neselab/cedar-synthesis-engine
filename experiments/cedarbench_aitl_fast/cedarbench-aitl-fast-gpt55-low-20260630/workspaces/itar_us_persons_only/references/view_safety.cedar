// Ceiling: view permitted only when EITHER
//   (a) principal is a US person (US_CITIZEN or LPR), OR
//   (b) the data is uncontrolled (not ITAR AND EAR99).
permit (
    principal is Engineer,
    action == Action::"view",
    resource is TechnicalData
)
when {
    (principal.citizenshipStatus == "US_CITIZEN" || principal.citizenshipStatus == "LPR")
    || (!resource.itarControlled && resource.earCategory == "EAR99")
};
