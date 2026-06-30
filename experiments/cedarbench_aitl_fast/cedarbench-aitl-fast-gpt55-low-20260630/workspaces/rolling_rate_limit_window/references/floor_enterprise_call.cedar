// Floor: an enterprise-tier client MUST be able to call any
// endpoint with no rate cap, provided the window is fresh.
permit (
    principal is Client,
    action == Action::"call",
    resource is Endpoint
)
when {
    !context.windowExpired
    && principal.tier == "enterprise"
};
