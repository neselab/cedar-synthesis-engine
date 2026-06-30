"""Hand-authored verification plan for realworld/embargo_by_region.

Regional release-window enforcement. Each Asset carries three release
datetimes (US, EU, APAC). The user's `region` selects which release
datetime applies. Cedar has no dynamic record key access, so the
candidate policy must branch explicitly on each region value.

The common failure modes this scenario hunts:
  - Candidate cross-wires regions (e.g. checks releaseEU for a US user).
  - Candidate forgets the 24h anti-leak buffer on download.
  - Candidate permits view/download for a region whose release datetime
    is still in the future.
  - Candidate uses a single release datetime for all regions instead of
    branching on the user's region.

8 checks total (2 ceilings + 4 floors + 2 liveness).
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # -- Safety ceilings ------------------------------------------------
        {
            "name": "view_safety",
            "description": "view permitted only when context.now >= the release datetime for the user's region",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"view"',
            "resource_type": "Asset",
            "reference_path": os.path.join(REFS, "view_safety.cedar"),
        },
        {
            "name": "download_safety",
            "description": "download permitted only when context.now >= release datetime for user's region PLUS 24h anti-leak buffer",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"download"',
            "resource_type": "Asset",
            "reference_path": os.path.join(REFS, "download_safety.cedar"),
        },

        # -- Floors (positive assertions) -----------------------------------
        {
            "name": "floor_view_us",
            "description": "US-region user MUST be able to view an asset once context.now >= releaseUS",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"view"',
            "resource_type": "Asset",
            "floor_path": os.path.join(REFS, "floor_view_us.cedar"),
        },
        {
            "name": "floor_view_eu",
            "description": "EU-region user MUST be able to view an asset once context.now >= releaseEU",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"view"',
            "resource_type": "Asset",
            "floor_path": os.path.join(REFS, "floor_view_eu.cedar"),
        },
        {
            "name": "floor_view_apac",
            "description": "APAC-region user MUST be able to view an asset once context.now >= releaseAPAC",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"view"',
            "resource_type": "Asset",
            "floor_path": os.path.join(REFS, "floor_view_apac.cedar"),
        },
        {
            "name": "floor_download_after_buffer",
            "description": "Any user MUST be able to download once context.now >= regional release + 24h buffer",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"download"',
            "resource_type": "Asset",
            "floor_path": os.path.join(REFS, "floor_download_after_buffer.cedar"),
        },

        # -- Liveness -------------------------------------------------------
        {
            "name": "liveness_view",
            "description": "User+view+Asset liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"view"',
            "resource_type": "Asset",
        },
        {
            "name": "liveness_download",
            "description": "User+download+Asset liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"download"',
            "resource_type": "Asset",
        },
    ]
