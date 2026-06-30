// Ceiling: explicit priority-ordered permit. Each lower-priority rule
// negates the trigger conditions of every higher-priority rule.
//   R1 (highest): legalHold       => legal_team only.
//   R2 (medium):  !legalHold && containsPII => pii_clearance only.
//   R3 (lowest):  !legalHold && !containsPII => role == "reader".
permit (
    principal is User,
    action == Action::"access",
    resource is Record
)
when {
    (resource.legalHold && principal.role == "legal_team")
    || (!resource.legalHold && resource.containsPII && principal.pii_clearance)
    || (!resource.legalHold && !resource.containsPII && principal.role == "reader")
};
