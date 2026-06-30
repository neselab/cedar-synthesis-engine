"""Hand-authored verification plan for realworld/ci_cd_deployment_gate.

CI/CD pipeline deployment authorization. Tests:
  - Environment-tiered role gating (dev < staging < production)
  - Boolean precondition on resource attribute (hasPassedTests)
  - Three distinct actions with different authorization surfaces
  - String equality on resource.environment for promotion tiers
  - Emergency rollback path (no test-pass requirement)
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # -- Safety ceilings (one per action) --------------------------------
        {
            "name": "deploy_safety",
            "description": (
                "deploy permitted only when tests passed AND "
                "(dev=any role, staging=lead/releaseManager, "
                "production=releaseManager)"
            ),
            "type": "implies",
            "principal_type": "PipelineUser",
            "action": 'Action::"deploy"',
            "resource_type": "Deployment",
            "reference_path": os.path.join(REFS, "deploy_safety.cedar"),
        },
        {
            "name": "rollback_safety",
            "description": "rollback permitted only when role is lead or releaseManager",
            "type": "implies",
            "principal_type": "PipelineUser",
            "action": 'Action::"rollback"',
            "resource_type": "Deployment",
            "reference_path": os.path.join(REFS, "rollback_safety.cedar"),
        },
        {
            "name": "approve_safety",
            "description": "approve permitted only when role is releaseManager",
            "type": "implies",
            "principal_type": "PipelineUser",
            "action": 'Action::"approve"',
            "resource_type": "Deployment",
            "reference_path": os.path.join(REFS, "approve_safety.cedar"),
        },

        # -- Floors -----------------------------------------------------------
        {
            "name": "dev_deploy_floor",
            "description": "Developer with passing tests MUST deploy to dev",
            "type": "floor",
            "principal_type": "PipelineUser",
            "action": 'Action::"deploy"',
            "resource_type": "Deployment",
            "floor_path": os.path.join(REFS, "dev_deploy_floor.cedar"),
        },
        {
            "name": "staging_deploy_floor",
            "description": "Lead with passing tests MUST deploy to staging",
            "type": "floor",
            "principal_type": "PipelineUser",
            "action": 'Action::"deploy"',
            "resource_type": "Deployment",
            "floor_path": os.path.join(REFS, "staging_deploy_floor.cedar"),
        },
        {
            "name": "prod_deploy_floor",
            "description": "releaseManager with passing tests MUST deploy to production",
            "type": "floor",
            "principal_type": "PipelineUser",
            "action": 'Action::"deploy"',
            "resource_type": "Deployment",
            "floor_path": os.path.join(REFS, "prod_deploy_floor.cedar"),
        },
        {
            "name": "rollback_floor",
            "description": "Lead MUST be permitted to rollback any environment",
            "type": "floor",
            "principal_type": "PipelineUser",
            "action": 'Action::"rollback"',
            "resource_type": "Deployment",
            "floor_path": os.path.join(REFS, "rollback_floor.cedar"),
        },
        {
            "name": "approve_floor",
            "description": "releaseManager MUST be permitted to approve",
            "type": "floor",
            "principal_type": "PipelineUser",
            "action": 'Action::"approve"',
            "resource_type": "Deployment",
            "floor_path": os.path.join(REFS, "approve_floor.cedar"),
        },

        # -- Liveness ---------------------------------------------------------
        {
            "name": "liveness_deploy",
            "description": "PipelineUser+deploy+Deployment liveness",
            "type": "always-denies-liveness",
            "principal_type": "PipelineUser",
            "action": 'Action::"deploy"',
            "resource_type": "Deployment",
        },
        {
            "name": "liveness_rollback",
            "description": "PipelineUser+rollback+Deployment liveness",
            "type": "always-denies-liveness",
            "principal_type": "PipelineUser",
            "action": 'Action::"rollback"',
            "resource_type": "Deployment",
        },
        {
            "name": "liveness_approve",
            "description": "PipelineUser+approve+Deployment liveness",
            "type": "always-denies-liveness",
            "principal_type": "PipelineUser",
            "action": 'Action::"approve"',
            "resource_type": "Deployment",
        },
    ]
