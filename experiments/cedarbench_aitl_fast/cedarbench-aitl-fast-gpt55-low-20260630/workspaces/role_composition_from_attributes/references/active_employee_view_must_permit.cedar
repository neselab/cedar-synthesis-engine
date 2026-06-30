// Floor: an active employee MUST be able to view any resource,
// regardless of seniority or certifications.
permit (
    principal is Employee,
    action == Action::"view",
    resource is Resource
)
when {
    principal.employmentStatus == "active"
};
