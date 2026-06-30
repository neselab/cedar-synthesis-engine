// Floor: any endpoint MUST be permitted to inspect any event.
// No conditions -- inspect is unconditionally permitted.
permit (
    principal is WebhookEndpoint,
    action == Action::"inspect",
    resource is Event
);
