// Floor: an employee satisfying ALL three manager predicates MUST
// be permitted to manage any resource:
//   - employmentStatus == "active",
//   - seniority >= 5,
//   - certifications.contains("MGMT-101").
// This is the effective-manager floor; no `principal.role` is
// involved.
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
