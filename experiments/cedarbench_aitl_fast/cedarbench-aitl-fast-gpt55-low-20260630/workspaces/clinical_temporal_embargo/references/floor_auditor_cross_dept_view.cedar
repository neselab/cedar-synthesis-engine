permit (
    principal is User,
    action == Action::"View",
    resource is Document
) when {
    principal in Role::"GlobalAuditor" &&
    principal in Role::"ClinicalResearcher" &&
    principal.clearanceLevel > 3 &&
    resource.classification != "HighlyRestricted" &&
    resource.projectStatus == "Active" &&
    context.requestTime >= resource.embargoUntil
};