// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
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

permit (
    principal is User,
    action in [Action::"View", Action::"Edit"],
    resource is Document
)
when {
    principal in Role::"DataManager" &&
    resource.projectStatus == "Active" &&
    principal.clearanceLevel > 5
};
