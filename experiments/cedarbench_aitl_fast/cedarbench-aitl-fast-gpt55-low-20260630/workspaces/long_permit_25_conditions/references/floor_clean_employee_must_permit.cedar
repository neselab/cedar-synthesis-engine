// Floor: a fully-credentialed employee with all 25 conditions satisfied
// MUST be permitted. The candidate must be at least as permissive as
// this floor.
//
// Concrete witness:
//   - role employee, MFA verified+fresh, clearance 3 ≥ requires 2,
//   - dept matches ownerDept, not archived, not contractor,
//   - compliance current, background check passed,
//   - VPN connected, risk 10, no incident, location office,
//   - classification "confidential" (not public, not restricted),
//   - resource requiresNda true, principal nda+nonDisclosureSigned true,
//   - resource complianceFlag true, principal compliance current.
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
    && context.currentLocation == "office"
    && resource.classification == "confidential"
    && principal.clearanceLevel >= 2
    && principal.clearanceLevel <= 5
    && resource.requiresClearance >= 1
    && resource.requiresNda
    && principal.nda
    && principal.nonDisclosureSigned
    && resource.complianceFlag
    && context.riskScore >= 0
    && principal.dept != ""
    && resource.ownerDept != ""
};
