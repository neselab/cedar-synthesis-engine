forbid (
    principal is User,
    action in [Action::"View", Action::"Edit"],
    resource is Document
)
when {
    principal.department != resource.projectManagingDepartment
}
unless {
    principal in Role::"GlobalAuditor"
};

forbid (
    principal is User,
    action in [Action::"View", Action::"Edit"],
    resource is Document
)
when {
    context.requestTime < resource.embargoUntil
}
unless {
    principal in Role::"PrincipalInvestigator"
};

permit (
    principal is User,
    action in [Action::"View", Action::"Edit"],
    resource is Document
)
when {
    principal in Role::"ClinicalResearcher" &&
    resource.projectStatus == "Active" &&
    principal.clearanceLevel > 3 &&
    resource.classification != "HighlyRestricted"
};

permit (
    principal is User,
    action in [Action::"View", Action::"Edit"],
    resource is Document
)
when {
    principal in Role::"PrincipalInvestigator" &&
    resource.projectStatus == "Active" &&
    context.networkRiskScore < 20 &&
    context.isCompliantDevice == true
};