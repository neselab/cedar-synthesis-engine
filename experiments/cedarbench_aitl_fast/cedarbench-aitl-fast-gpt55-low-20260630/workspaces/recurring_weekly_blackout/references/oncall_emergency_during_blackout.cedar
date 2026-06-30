// Floor: an oncall user MUST be able to perform `emergencyAccess`
// when the host attests we ARE inside a blackout window.
permit (
    principal is User,
    action == Action::"emergencyAccess",
    resource is System
)
when {
    principal.role == "oncall"
    && context.inBlackoutWindow == true
};
