// Ceiling: retry permitted only when ALL of:
//  - endpoint is verified,
//  - event type is in endpoint's allowed set,
//  - event is NOT internal.
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
