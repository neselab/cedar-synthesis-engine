// Floor: a user with clearance "internal" or higher MUST be permitted
// to export an internal dataset that does NOT contain personal data.
//
// Per section 8.8: floor must be jointly satisfiable with the export ceiling,
// which requires !hasPersonalData; therefore we include that constraint here.
permit (
    principal is User,
    action == Action::"export",
    resource is Dataset
)
when {
    (principal.clearance == "internal" || principal.clearance == "restricted")
    && resource.classification == "internal"
    && !resource.hasPersonalData
};
