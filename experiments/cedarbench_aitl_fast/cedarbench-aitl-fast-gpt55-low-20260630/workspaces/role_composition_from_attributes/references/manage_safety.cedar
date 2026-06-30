// Ceiling: manage permitted ONLY when the principal qualifies as
// an effective manager — ALL three predicates hold simultaneously:
//   - employmentStatus == "active",
//   - seniority >= 5,
//   - certifications.contains("MGMT-101").
// There is NO `principal.role` attribute to check; the manager
// role is computed inline from the attribute conjunction.
permit (
    principal is Employee,
    action == Action::"manage",
    resource is Resource
)
when {
    principal.employmentStatus == "active"
    && principal.seniority >= 5
    && principal.certifications.contains("MGMT-101")
};
