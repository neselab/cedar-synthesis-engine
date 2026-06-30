permit (
    principal is Engineer,
    action == Action::"view",
    resource is TechnicalData
)
when {
    principal.citizenshipStatus == "US_CITIZEN" ||
    principal.citizenshipStatus == "LPR" ||
    (
        resource.itarControlled == false &&
        resource.earCategory == "EAR99"
    )
};

permit (
    principal is Engineer,
    action == Action::"download",
    resource is TechnicalData
)
when {
    (
        principal.citizenshipStatus == "US_CITIZEN" ||
        principal.citizenshipStatus == "LPR" ||
        (
            resource.itarControlled == false &&
            resource.earCategory == "EAR99"
        )
    ) &&
    (
        resource.itarControlled == false ||
        context.accessLocation == "US"
    )
};

permit (
    principal is Engineer,
    action == Action::"export",
    resource is TechnicalData
)
when {
    (
        principal.citizenshipStatus == "US_CITIZEN" ||
        principal.citizenshipStatus == "LPR"
    ) &&
    principal.clearanceVerified == true &&
    context.accessLocation == "US"
};