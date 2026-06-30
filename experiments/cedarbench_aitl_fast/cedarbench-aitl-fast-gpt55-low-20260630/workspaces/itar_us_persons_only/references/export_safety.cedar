// Ceiling: export permitted only when ALL of:
//   (a) principal is a US person (US_CITIZEN or LPR);
//   (b) clearanceVerified == true;
//   (c) accessLocation == "US".
permit (
    principal is Engineer,
    action == Action::"export",
    resource is TechnicalData
)
when {
    (principal.citizenshipStatus == "US_CITIZEN" || principal.citizenshipStatus == "LPR")
    && principal.clearanceVerified
    && context.accessLocation == "US"
};
