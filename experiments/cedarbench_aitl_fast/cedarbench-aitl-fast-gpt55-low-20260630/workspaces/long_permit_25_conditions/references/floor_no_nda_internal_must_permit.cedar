// Floor: an employee accessing an INTERNAL document that does NOT
// require NDA and has NO compliance flag MUST be permitted, even if
// the principal hasn't signed an NDA — the polarity of `requiresNda`
// must be respected (a candidate that gates on `principal.nda`
// unconditionally would fail this floor).
//
// Concrete witness:
//   - role employee, MFA verified+fresh, clearance 4 ≥ requires 1,
//   - dept matches, not archived, not contractor, compliance current,
//   - background check passed, VPN, risk 0, no incident, location home,
//   - classification "internal", requiresNda false, complianceFlag false.
permit (
    principal is User,
    action == Action::"accessSensitive",
    resource is Resource
)
when {
    principal.role == "employee"
    && principal.mfaVerified
    && context.now.durationSince(context.mfaTimestamp) < duration("1h")
    && principal.clearanceLevel >= resource.requiresClearance
    && principal.dept == resource.ownerDept
    && !resource.archived
    && !principal.isContractor
    && principal.complianceTrainingCurrent
    && principal.backgroundCheckPassed
    && context.vpnConnected
    && context.riskScore <= 50
    && !context.incidentMode
    && context.currentLocation == "home"
    && resource.classification == "internal"
    && principal.clearanceLevel >= 2
    && principal.clearanceLevel <= 5
    && resource.requiresClearance >= 1
    && !resource.requiresNda
    && !resource.complianceFlag
    && context.riskScore >= 0
    && principal.dept != ""
    && resource.ownerDept != ""
};
