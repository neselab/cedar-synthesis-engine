// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
forbid (
    principal is User,
    action in [Action::"View", Action::"Edit"],
    resource is Document
)
when {
    resource.projectStatus != "Active"
};

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
    action == Action::"Edit",
    resource is Document
)
when {
    context.hasPatientConsent == false
};

permit (
    principal is User,
    action in [Action::"View", Action::"Edit"],
    resource is Document
)
when {
    principal in Role::"ClinicalResearcher" &&
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
    context.networkRiskScore < 20 &&
    context.isCompliantDevice == true
};
