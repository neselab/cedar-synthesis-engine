permit (
    principal is User,
    action == Action::"access",
    resource is Record
)
when {
    resource.legalHold == true &&
    principal.role == "legal_team"
};

permit (
    principal is User,
    action == Action::"access",
    resource is Record
)
when {
    resource.legalHold == false &&
    resource.containsPII == true &&
    principal.pii_clearance == true
};

permit (
    principal is User,
    action == Action::"access",
    resource is Record
)
when {
    resource.legalHold == false &&
    resource.containsPII == false &&
    principal.role == "reader"
};