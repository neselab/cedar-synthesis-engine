---
pattern: webhook signature verification
difficulty: medium
features:
  - non-User principal (WebhookEndpoint)
  - boolean attestation
  - scope-based action filtering
domain: API platform
synthesis_difficulty: 2
---

# Webhook Signature Verification -- Outbound M2M Delivery Authorization

## Context

This scenario models an API platform that delivers outbound webhook events
to registered endpoints. The principal is a `WebhookEndpoint` -- a
machine-to-machine actor, not a human user. Each endpoint declares a set
of event types it is subscribed to (`allowedEvents`) and a boolean
`isVerified` flag indicating whether its HMAC signature has been validated
by the platform's verification handshake.

Events (`Event`) are the resources being delivered. Each event has an
`eventType` string and an `isInternal` boolean flag. Internal events
are platform-internal telemetry that must never be delivered to external
endpoints.

## Actions

- **deliver** -- send the event payload to the endpoint.
- **retry** -- re-deliver a previously failed event to the endpoint.
- **inspect** -- read event metadata for debugging (does NOT deliver the
  payload).

## Requirements

### Action: deliver

An event may be delivered to an endpoint when ALL of:

1. The endpoint is verified: `principal.isVerified == true`.
2. The event type is in the endpoint's allowed set:
   `principal.allowedEvents.contains(resource.eventType)`.
3. The event is NOT internal: `resource.isInternal == false`.

Floor: a verified endpoint whose `allowedEvents` contains the event's
type MUST be permitted to receive delivery of a non-internal event.

### Action: retry

Re-delivery has the same authorization requirements as initial delivery:

1. The endpoint is verified.
2. The event type is in the endpoint's allowed set.
3. The event is NOT internal.

Floor: a verified endpoint whose `allowedEvents` contains the event's
type MUST be permitted to retry a non-internal event.

### Action: inspect

Any endpoint (verified or not) may inspect any event (internal or not).
This is a read-only debugging action with no delivery of the payload.

Floor: any endpoint MUST be permitted to inspect any event.

### Liveness

Each of the three actions must permit at least one request.

## Out of scope

- No rate-limiting or retry-count constraints.
- No temporal attributes (expiry, cooldown windows).
- No organization / tenant isolation.
- No global forbids.
