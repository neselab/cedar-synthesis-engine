"""Verification plan for realworld/action_with_many_principals.
Universal API gateway: a single `invoke` action that accepts 6 distinct
principal entity types. Tests `is`-narrowing across N types so each
type-specific attribute is read only after its `is` check.
"""
import os
REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")

def get_checks():
    return [
        {
            "name": "ceiling_invoke",
            "description": "invoke permitted only when the per-type predicate holds",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"invoke"',
            "resource_type": "Resource",
            "reference_path": os.path.join(REFS, "ceiling_invoke.cedar"),
        },
        {
            "name": "floor_user_mfa",
            "description": "mfa-verified User MUST be permitted to invoke",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"invoke"',
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, "floor_user_mfa.cedar"),
        },
        {
            "name": "floor_apikey_scope",
            "description": "ApiKey with invoke scope MUST be permitted",
            "type": "floor",
            "principal_type": "ApiKey",
            "action": 'Action::"invoke"',
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, "floor_apikey_scope.cedar"),
        },
        {
            "name": "floor_serviceaccount_named",
            "description": "ServiceAccount with non-empty serviceName MUST be permitted",
            "type": "floor",
            "principal_type": "ServiceAccount",
            "action": 'Action::"invoke"',
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, "floor_serviceaccount_named.cedar"),
        },
        {
            "name": "floor_webhook_signed",
            "description": "Webhook with valid signature MUST be permitted",
            "type": "floor",
            "principal_type": "Webhook",
            "action": 'Action::"invoke"',
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, "floor_webhook_signed.cedar"),
        },
        {
            "name": "floor_batchjob",
            "description": "any BatchJob MUST be permitted (no per-request gate)",
            "type": "floor",
            "principal_type": "BatchJob",
            "action": 'Action::"invoke"',
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, "floor_batchjob.cedar"),
        },
        {
            "name": "floor_scheduler_cron",
            "description": "Scheduler with cronVerified MUST be permitted",
            "type": "floor",
            "principal_type": "Scheduler",
            "action": 'Action::"invoke"',
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, "floor_scheduler_cron.cedar"),
        },
        {
            "name": "liveness_invoke",
            "description": "at least one invoke request must be permitted",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"invoke"',
            "resource_type": "Resource",
        },
    ]
