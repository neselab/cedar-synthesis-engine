// Floor: a verified endpoint whose allowedEvents contains the event's
// type MUST be permitted to retry a non-internal event.
// No global forbids in this scenario, so the floor mirrors the ceiling.
permit (
    principal is WebhookEndpoint,
    action == Action::"retry",
    resource is Event
)
when {
    principal.isVerified
    && principal.allowedEvents.contains(resource.eventType)
    && !resource.isInternal
};
