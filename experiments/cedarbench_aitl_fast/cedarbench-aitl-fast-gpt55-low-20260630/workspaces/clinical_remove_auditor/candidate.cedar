forbid (
    principal is User,
    action == Action::"View",
    resource is Document
)
when {
    principal.department != resource.projectManagingDepartment
};

forbid (
    principal is User,
    action == Action::"Edit",
    resource is Document
)
when {
    principal.department != resource.projectManagingDepartment
};

forbid (
    principal is User,
    action == Action::"View",
    resource is Document
)
when {
    resource.projectStatus != "Active"
};

forbid (
    principal is User,
    action == Action::"Edit",
    resource is Document
)
when {
    resource.projectStatus != "Active"
};

permit (
    principal is User,
    action == Action::"View",
    resource is Document
)
when {
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
    principal in Role::"PrincipalInvestigator" &&
    context.networkRiskScore < 20 &&
    context.isCompliantDevice == true
};