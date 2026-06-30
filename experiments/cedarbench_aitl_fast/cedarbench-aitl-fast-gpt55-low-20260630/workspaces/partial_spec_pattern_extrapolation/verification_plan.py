"""Hand-authored verification plan for realworld/partial_spec_pattern_extrapolation.

The spec describes junior_dev and senior_dev fully but only describes
lead_dev as a delta against senior_dev ("extends senior_dev with merge
+ manageBranches"). The planner must extrapolate that lead_dev inherits
ALL senior_dev permissions in addition to the two new actions.

Failure modes hunted by this scenario:
  - Candidate forgets lead_dev inherits read/write/review from
    senior_dev and only grants merge + manageBranches. Caught by
    floor_lead_write_any (read/review floors are also implied).
  - Candidate over-permits and lets senior_dev or junior_dev merge or
    manage branches. Caught by merge_ceiling and manage_branches_ceiling.
  - Candidate over-permits and lets junior_dev review. Caught by
    review_ceiling.
  - Candidate forgets the junior_dev project restriction and lets
    junior_dev read/write any project. Caught by read_ceiling and
    write_ceiling.
  - Candidate fails to handle unrecognized roles and lets them slip
    through (would violate the ceilings since the role guards
    enumerate exactly the three known roles).

5 ceilings + 6 floors + 5 liveness = 16 checks total.
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # -- Safety ceilings ------------------------------------------------
        {
            "name": "read_ceiling",
            "description": "read permitted only for junior_dev on own project, senior_dev (any), or lead_dev (any, inherited)",
            "type": "implies",
            "principal_type": "Developer",
            "action": 'Action::"read"',
            "resource_type": "CodeArtifact",
            "reference_path": os.path.join(REFS, "read_ceiling.cedar"),
        },
        {
            "name": "write_ceiling",
            "description": "write permitted only for junior_dev on own project, senior_dev (any), or lead_dev (any, inherited)",
            "type": "implies",
            "principal_type": "Developer",
            "action": 'Action::"write"',
            "resource_type": "CodeArtifact",
            "reference_path": os.path.join(REFS, "write_ceiling.cedar"),
        },
        {
            "name": "review_ceiling",
            "description": "review permitted only for senior_dev or lead_dev (lead_dev inherits)",
            "type": "implies",
            "principal_type": "Developer",
            "action": 'Action::"review"',
            "resource_type": "CodeArtifact",
            "reference_path": os.path.join(REFS, "review_ceiling.cedar"),
        },
        {
            "name": "merge_ceiling",
            "description": "merge permitted ONLY for lead_dev (extrapolated lead-only privilege)",
            "type": "implies",
            "principal_type": "Developer",
            "action": 'Action::"merge"',
            "resource_type": "CodeArtifact",
            "reference_path": os.path.join(REFS, "merge_ceiling.cedar"),
        },
        {
            "name": "manage_branches_ceiling",
            "description": "manageBranches permitted ONLY for lead_dev (extrapolated lead-only privilege)",
            "type": "implies",
            "principal_type": "Developer",
            "action": 'Action::"manageBranches"',
            "resource_type": "CodeArtifact",
            "reference_path": os.path.join(REFS, "manage_branches_ceiling.cedar"),
        },

        # -- Floors (positive assertions) -----------------------------------
        {
            "name": "floor_junior_read_own",
            "description": "junior_dev MUST be permitted to read CodeArtifact whose project matches their assignedProject",
            "type": "floor",
            "principal_type": "Developer",
            "action": 'Action::"read"',
            "resource_type": "CodeArtifact",
            "floor_path": os.path.join(REFS, "floor_junior_read_own.cedar"),
        },
        {
            "name": "floor_senior_read_any",
            "description": "senior_dev MUST be permitted to read any CodeArtifact regardless of project",
            "type": "floor",
            "principal_type": "Developer",
            "action": 'Action::"read"',
            "resource_type": "CodeArtifact",
            "floor_path": os.path.join(REFS, "floor_senior_read_any.cedar"),
        },
        {
            "name": "floor_senior_review_any",
            "description": "senior_dev MUST be permitted to review any CodeArtifact",
            "type": "floor",
            "principal_type": "Developer",
            "action": 'Action::"review"',
            "resource_type": "CodeArtifact",
            "floor_path": os.path.join(REFS, "floor_senior_review_any.cedar"),
        },
        {
            "name": "floor_lead_write_any",
            "description": "lead_dev MUST be permitted to write any CodeArtifact (inherited from senior_dev -- extrapolation check)",
            "type": "floor",
            "principal_type": "Developer",
            "action": 'Action::"write"',
            "resource_type": "CodeArtifact",
            "floor_path": os.path.join(REFS, "floor_lead_write_any.cedar"),
        },
        {
            "name": "floor_lead_merge",
            "description": "lead_dev MUST be permitted to merge any CodeArtifact (extrapolated delta permission)",
            "type": "floor",
            "principal_type": "Developer",
            "action": 'Action::"merge"',
            "resource_type": "CodeArtifact",
            "floor_path": os.path.join(REFS, "floor_lead_merge.cedar"),
        },
        {
            "name": "floor_lead_manage_branches",
            "description": "lead_dev MUST be permitted to manageBranches on any CodeArtifact (extrapolated delta permission)",
            "type": "floor",
            "principal_type": "Developer",
            "action": 'Action::"manageBranches"',
            "resource_type": "CodeArtifact",
            "floor_path": os.path.join(REFS, "floor_lead_manage_branches.cedar"),
        },

        # -- Liveness -------------------------------------------------------
        {
            "name": "liveness_read",
            "description": "Developer+read+CodeArtifact liveness",
            "type": "always-denies-liveness",
            "principal_type": "Developer",
            "action": 'Action::"read"',
            "resource_type": "CodeArtifact",
        },
        {
            "name": "liveness_write",
            "description": "Developer+write+CodeArtifact liveness",
            "type": "always-denies-liveness",
            "principal_type": "Developer",
            "action": 'Action::"write"',
            "resource_type": "CodeArtifact",
        },
        {
            "name": "liveness_review",
            "description": "Developer+review+CodeArtifact liveness",
            "type": "always-denies-liveness",
            "principal_type": "Developer",
            "action": 'Action::"review"',
            "resource_type": "CodeArtifact",
        },
        {
            "name": "liveness_merge",
            "description": "Developer+merge+CodeArtifact liveness",
            "type": "always-denies-liveness",
            "principal_type": "Developer",
            "action": 'Action::"merge"',
            "resource_type": "CodeArtifact",
        },
        {
            "name": "liveness_manage_branches",
            "description": "Developer+manageBranches+CodeArtifact liveness",
            "type": "always-denies-liveness",
            "principal_type": "Developer",
            "action": 'Action::"manageBranches"',
            "resource_type": "CodeArtifact",
        },
    ]
