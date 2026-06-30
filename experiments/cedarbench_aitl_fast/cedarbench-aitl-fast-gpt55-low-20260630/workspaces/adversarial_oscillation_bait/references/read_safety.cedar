// CEILING for `read`. Permitted only when one of:
//   1. principal.role == "admin"
//   2. owner bypass with MFA-on-confidential carve-out
//   3. user-role, !isContractor, non-confidential
//   4. user-role, isContractor, confidential, MFA verified
permit (
    principal is User,
    action == Action::"read",
    resource is Resource
)
when {
    principal.role == "admin"
    || (
        principal == resource.owner
        && (resource.classification != "confidential" || context.mfaVerified)
    )
    || (
        principal.role == "user"
        && principal.isContractor == false
        && resource.classification != "confidential"
    )
    || (
        principal.role == "user"
        && principal.isContractor == true
        && resource.classification == "confidential"
        && context.mfaVerified == true
    )
};
