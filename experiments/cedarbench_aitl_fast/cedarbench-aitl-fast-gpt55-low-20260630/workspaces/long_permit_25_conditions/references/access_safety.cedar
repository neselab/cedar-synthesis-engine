// Ceiling: accessSensitive permitted ONLY when every one of the 25
// AND-chained conditions holds. Candidate must be no more permissive
// than this conjunction.
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
    && context.currentLocation != "travel"
    && resource.classification != "public"
    && resource.classification != "restricted"
    && principal.clearanceLevel >= 2
    && principal.clearanceLevel <= 5
    && resource.requiresClearance >= 1
    && ((!resource.requiresNda) || principal.nda)
    && ((!resource.requiresNda) || principal.nonDisclosureSigned)
    && ((!resource.complianceFlag) || principal.complianceTrainingCurrent)
    && context.riskScore >= 0
    && principal.dept != ""
    && resource.ownerDept != ""
    && principal.mfaVerified && context.vpnConnected
};
