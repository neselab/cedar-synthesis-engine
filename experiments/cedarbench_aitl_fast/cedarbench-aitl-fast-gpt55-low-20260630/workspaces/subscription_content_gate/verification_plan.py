"""Hand-authored verification plan for realworld/subscription_content_gate.

Subscription-based content access for streaming / SaaS platforms. Tests:
  - String-enum hierarchy (plan vs content tier: free < basic < premium)
  - Preview bypass that applies only to streaming, not downloading
  - Action variants with different plan requirements (stream vs download
    vs share)
  - Disjunctive tier encoding (Cedar has no enum ordering)
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # -- Safety ceilings (one per action) ---------------------------------
        {
            "name": "stream_safety",
            "description": "stream permitted only when active AND (preview OR plan >= tier)",
            "type": "implies",
            "principal_type": "Subscriber",
            "action": 'Action::"stream"',
            "resource_type": "Content",
            "reference_path": os.path.join(REFS, "stream_safety.cedar"),
        },
        {
            "name": "download_safety",
            "description": "download permitted only when active AND plan in {basic,premium} AND plan >= tier",
            "type": "implies",
            "principal_type": "Subscriber",
            "action": 'Action::"download"',
            "resource_type": "Content",
            "reference_path": os.path.join(REFS, "download_safety.cedar"),
        },
        {
            "name": "share_safety",
            "description": "share permitted only when active AND plan == premium",
            "type": "implies",
            "principal_type": "Subscriber",
            "action": 'Action::"share"',
            "resource_type": "Content",
            "reference_path": os.path.join(REFS, "share_safety.cedar"),
        },

        # -- Floors ------------------------------------------------------------
        {
            "name": "free_must_stream_preview",
            "description": "Active free subscriber MUST stream preview content",
            "type": "floor",
            "principal_type": "Subscriber",
            "action": 'Action::"stream"',
            "resource_type": "Content",
            "floor_path": os.path.join(REFS, "free_must_stream_preview.cedar"),
        },
        {
            "name": "premium_must_stream_premium",
            "description": "Active premium subscriber MUST stream premium non-preview content",
            "type": "floor",
            "principal_type": "Subscriber",
            "action": 'Action::"stream"',
            "resource_type": "Content",
            "floor_path": os.path.join(REFS, "premium_must_stream_premium.cedar"),
        },
        {
            "name": "basic_must_download_free",
            "description": "Active basic subscriber MUST download free-tier content",
            "type": "floor",
            "principal_type": "Subscriber",
            "action": 'Action::"download"',
            "resource_type": "Content",
            "floor_path": os.path.join(REFS, "basic_must_download_free.cedar"),
        },
        {
            "name": "premium_must_share",
            "description": "Active premium subscriber MUST share content",
            "type": "floor",
            "principal_type": "Subscriber",
            "action": 'Action::"share"',
            "resource_type": "Content",
            "floor_path": os.path.join(REFS, "premium_must_share.cedar"),
        },

        # -- Liveness ----------------------------------------------------------
        {
            "name": "liveness_stream",
            "description": "Subscriber+stream+Content liveness",
            "type": "always-denies-liveness",
            "principal_type": "Subscriber",
            "action": 'Action::"stream"',
            "resource_type": "Content",
        },
        {
            "name": "liveness_download",
            "description": "Subscriber+download+Content liveness",
            "type": "always-denies-liveness",
            "principal_type": "Subscriber",
            "action": 'Action::"download"',
            "resource_type": "Content",
        },
        {
            "name": "liveness_share",
            "description": "Subscriber+share+Content liveness",
            "type": "always-denies-liveness",
            "principal_type": "Subscriber",
            "action": 'Action::"share"',
            "resource_type": "Content",
        },
    ]
