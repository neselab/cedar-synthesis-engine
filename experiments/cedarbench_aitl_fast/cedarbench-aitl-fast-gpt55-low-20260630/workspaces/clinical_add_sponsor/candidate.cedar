forbid (
    principal is User,
    action == Action::"View",
    resource is Document
)
when {
    principal.department != resource.projectManagingDepartment
}
unless {
    principal in Role::"GlobalAuditor" ||
    principal in Role::"SponsorRepresentative"
};

forbid (
    principal is User,
    action == Action::"Edit",
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
    principal in Role::"ClinicalResearcher" &&
    resource.projectStatus == "Active" &&
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
    resource.projectStatus == "Active" &&
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
    resource.projectStatus == "Active" &&
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
    resource.projectStatus == "Active" &&
    context.networkRiskScore < 20 &&
    context.isCompliantDevice == true
};

permit (
    principal is User,
    action == Action::"View",
    resource is Document
)
when {
    principal in Role::"SponsorRepresentative" &&
    resource.projectStatus == "Active" &&
    resource.studyPhase == "Phase-3"
};