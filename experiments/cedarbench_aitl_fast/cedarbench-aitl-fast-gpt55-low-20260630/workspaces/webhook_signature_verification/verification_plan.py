"""Hand-authored verification plan for realworld/webhook_signature_verification.

Outbound M2M webhook delivery authorization. Tests:
  - Non-User principal type (WebhookEndpoint)
  - Boolean attestation gate (isVerified)
  - Scope-based action filtering via Set<String> membership
  - Boolean resource flag (isInternal) as a delivery blocker
  - Unconditionally open action (inspect) alongside restricted ones

9 checks: 3 ceilings + 3 floors + 3 liveness.
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # -- Safety ceilings (one per action) ---------------------------------
        {
            "name": "deliver_safety",
            "description": "deliver permitted only when (verified, allowedEvents contains eventType, NOT internal)",
            "type": "implies",
            "principal_type": "WebhookEndpoint",
            "action": 'Action::"deliver"',
            "resource_type": "Event",
            "reference_path": os.path.join(REFS, "deliver_safety.cedar"),
        },
        {
            "name": "retry_safety",
            "description": "retry permitted only when (verified, allowedEvents contains eventType, NOT internal)",
            "type": "implies",
            "principal_type": "WebhookEndpoint",
            "action": 'Action::"retry"',
            "resource_type": "Event",
            "reference_path": os.path.join(REFS, "retry_safety.cedar"),
        },
        {
            "name": "inspect_safety",
            "description": "inspect permitted for any endpoint on any event (no restrictions)",
            "type": "implies",
            "principal_type": "WebhookEndpoint",
            "action": 'Action::"inspect"',
            "resource_type": "Event",
            "reference_path": os.path.join(REFS, "inspect_safety.cedar"),
        },

        # -- Floors ------------------------------------------------------------
        {
            "name": "verified_endpoint_must_deliver",
            "description": "Verified endpoint with matching allowedEvents MUST deliver non-internal event",
            "type": "floor",
            "principal_type": "WebhookEndpoint",
            "action": 'Action::"deliver"',
            "resource_type": "Event",
            "floor_path": os.path.join(REFS, "verified_endpoint_must_deliver.cedar"),
        },
        {
            "name": "verified_endpoint_must_retry",
            "description": "Verified endpoint with matching allowedEvents MUST retry non-internal event",
            "type": "floor",
            "principal_type": "WebhookEndpoint",
            "action": 'Action::"retry"',
            "resource_type": "Event",
            "floor_path": os.path.join(REFS, "verified_endpoint_must_retry.cedar"),
        },
        {
            "name": "any_endpoint_must_inspect",
            "description": "Any endpoint MUST be permitted to inspect any event",
            "type": "floor",
            "principal_type": "WebhookEndpoint",
            "action": 'Action::"inspect"',
            "resource_type": "Event",
            "floor_path": os.path.join(REFS, "any_endpoint_must_inspect.cedar"),
        },

        # -- Liveness ----------------------------------------------------------
        {
            "name": "liveness_deliver",
            "description": "WebhookEndpoint+deliver+Event liveness",
            "type": "always-denies-liveness",
            "principal_type": "WebhookEndpoint",
            "action": 'Action::"deliver"',
            "resource_type": "Event",
        },
        {
            "name": "liveness_retry",
            "description": "WebhookEndpoint+retry+Event liveness",
            "type": "always-denies-liveness",
            "principal_type": "WebhookEndpoint",
            "action": 'Action::"retry"',
            "resource_type": "Event",
        },
        {
            "name": "liveness_inspect",
            "description": "WebhookEndpoint+inspect+Event liveness",
            "type": "always-denies-liveness",
            "principal_type": "WebhookEndpoint",
            "action": 'Action::"inspect"',
            "resource_type": "Event",
        },
    ]
