// Ceiling: inspect permitted for any endpoint on any event.
// No restrictions -- debugging action has no delivery side-effect.
permit (
    principal is WebhookEndpoint,
    action == Action::"inspect",
    resource is Event
);
