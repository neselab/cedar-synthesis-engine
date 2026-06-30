permit (
    principal is Employee,
    action == Action::"view",
    resource is Resource
)
when {
    principal.employmentStatus == "active"
};

permit (
    principal is Employee,
    action == Action::"manage",
    resource is Resource
)
when {
    principal.employmentStatus == "active" &&
    principal.seniority >= 5 &&
    principal.certifications.contains("MGMT-101")
};