// Ceiling: download permitted only when ALL of:
//   (a) principal is a US person, OR data is uncontrolled (EAR99 + not ITAR);
//   (b) if the data is ITAR-controlled, accessLocation must be "US"
//       (deemed-export rule applies even to US persons).
permit (
    principal is Engineer,
    action == Action::"download",
    resource is TechnicalData
)
when {
    (
        (principal.citizenshipStatus == "US_CITIZEN" || principal.citizenshipStatus == "LPR")
        || (!resource.itarControlled && resource.earCategory == "EAR99")
    )
    && (!resource.itarControlled || context.accessLocation == "US")
};
