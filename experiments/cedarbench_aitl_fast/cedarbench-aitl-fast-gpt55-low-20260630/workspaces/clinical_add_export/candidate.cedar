forbid (
    principal is User,
    action in [Action::"View", Action::"Edit", Action::"Export"],
    resource is Document
)
when {
    principal.department != resource.projectManagingDepartment
}
unless {
    principal in Role::"GlobalAuditor"
};

permit (
    principal is User,
    action == Action::"View",
    resource is Document
)
when {
    resource.projectStatus == "Active" &&
    principal in Role::"ClinicalResearcher" &&
    principal.clearanceLevel > 3 &&
    resource.classification != "HighlyRestricted"
};

permit (
    principal is User,
    action == Action::"View",
    resource is Document
)
when {
    resource.projectStatus == "Active" &&
    principal in Role::"PrincipalInvestigator" &&
    context.networkRiskScore < 20 &&
    context.isCompliantDevice == true
};

permit (
    principal is User,
    action == Action::"Edit",
    resource is Document
)
when {
    resource.projectStatus == "Active" &&
    principal in Role::"ClinicalResearcher" &&
    principal.clearanceLevel > 3 &&
    resource.classification != "HighlyRestricted"
};

permit (
    principal is User,
    action == Action::"Edit",
    resource is Document
)
when {
    resource.projectStatus == "Active" &&
    principal in Role::"PrincipalInvestigator" &&
    context.networkRiskScore < 20 &&
    context.isCompliantDevice == true
};

permit (
    principal is User,
    action == Action::"Export",
    resource is Document
)
when {
    resource.projectStatus == "Active" &&
    principal in Role::"ClinicalResearcher" &&
    principal.clearanceLevel > 3 &&
    resource.classification != "HighlyRestricted" &&
    context.isCompliantDevice == true
};

permit (
    principal is User,
    action == Action::"Export",
    resource is Document
)
when {
    resource.projectStatus == "Active" &&
    principal in Role::"PrincipalInvestigator" &&
    context.networkRiskScore < 20 &&
    context.isCompliantDevice == true
};