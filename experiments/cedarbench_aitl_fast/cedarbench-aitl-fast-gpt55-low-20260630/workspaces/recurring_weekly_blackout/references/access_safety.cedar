// Ceiling: `access` is permitted only when the principal is oncall
// (any time) OR the host attests we are NOT in a blackout window.
permit (
    principal is User,
    action == Action::"access",
    resource is System
)
when {
    principal.role == "oncall"
    || context.inBlackoutWindow == false
};
