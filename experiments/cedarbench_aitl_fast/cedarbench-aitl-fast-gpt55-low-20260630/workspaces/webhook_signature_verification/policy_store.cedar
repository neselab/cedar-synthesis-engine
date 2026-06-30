// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
permit (
    principal is WebhookEndpoint,
    action == Action::"deliver",
    resource is Event
)
when {
    principal.isVerified == true &&
    principal.allowedEvents.contains(resource.eventType) &&
    resource.isInternal == false
};

permit (
    principal is WebhookEndpoint,
    action == Action::"retry",
    resource is Event
)
when {
    principal.isVerified == true &&
    principal.allowedEvents.contains(resource.eventType) &&
    resource.isInternal == false
};

permit (
    principal is WebhookEndpoint,
    action == Action::"inspect",
    resource is Event
);
