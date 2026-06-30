// Ceiling: `emergencyAccess` is permitted only when the principal is
// oncall AND the host attests we are inside a blackout window.
permit (
    principal is User,
    action == Action::"emergencyAccess",
    resource is System
)
when {
    principal.role == "oncall"
    && context.inBlackoutWindow == true
};
