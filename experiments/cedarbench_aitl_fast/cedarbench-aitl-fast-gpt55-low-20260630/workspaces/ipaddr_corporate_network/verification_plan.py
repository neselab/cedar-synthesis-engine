"""Hand-authored verification plan for realworld/ipaddr_corporate_network.

First scenario in CedarBench exercising Cedar's `ipaddr` extension type
(`ip("...")`, `.isInRange(...)`). The plan encodes three orthogonal
safety properties (one per action) and four positive floors.

The compromised-range exclusion is a global safety property repeated in
every floor for §8.8 floor-bound consistency.

10 checks total (3 ceilings + 4 floors + 3 liveness).
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # -- Safety ceilings ------------------------------------------------
        {
            "name": "access_safety",
            "description": (
                "access permitted only when sourceIp is in a corporate range "
                "(10/8, 172.16/12, 192.168/16) AND not in compromised range "
                "(10.50.0.0/16) AND, if resource.requiresVpn, additionally "
                "in the VPN segment (10.10.0.0/16)"
            ),
            "type": "implies",
            "principal_type": "Employee",
            "action": 'Action::"access"',
            "resource_type": "InternalSystem",
            "reference_path": os.path.join(REFS, "access_safety.cedar"),
        },
        {
            "name": "configure_safety",
            "description": (
                "configure permitted only when role is ops/admin AND sourceIp "
                "is in admin subnet (10.20.0.0/24) AND not in compromised "
                "range (10.50.0.0/16)"
            ),
            "type": "implies",
            "principal_type": "Employee",
            "action": 'Action::"configure"',
            "resource_type": "InternalSystem",
            "reference_path": os.path.join(REFS, "configure_safety.cedar"),
        },
        {
            "name": "emergency_safety",
            "description": "emergencyAccess permitted only when role is admin",
            "type": "implies",
            "principal_type": "Employee",
            "action": 'Action::"emergencyAccess"',
            "resource_type": "InternalSystem",
            "reference_path": os.path.join(REFS, "emergency_safety.cedar"),
        },

        # -- Floors (positive assertions) -----------------------------------
        {
            "name": "standard_corp_access",
            "description": (
                "A standard Employee from a corporate range MUST access a "
                "non-VPN InternalSystem (when sourceIp is not compromised)"
            ),
            "type": "floor",
            "principal_type": "Employee",
            "action": 'Action::"access"',
            "resource_type": "InternalSystem",
            "floor_path": os.path.join(REFS, "standard_corp_access.cedar"),
        },
        {
            "name": "vpn_required_access",
            "description": (
                "An Employee on the VPN segment MUST access a VPN-required "
                "InternalSystem (when sourceIp is not compromised)"
            ),
            "type": "floor",
            "principal_type": "Employee",
            "action": 'Action::"access"',
            "resource_type": "InternalSystem",
            "floor_path": os.path.join(REFS, "vpn_required_access.cedar"),
        },
        {
            "name": "ops_admin_subnet_configure",
            "description": (
                "An ops Employee from the admin subnet (10.20.0.0/24) MUST "
                "be able to configure an InternalSystem"
            ),
            "type": "floor",
            "principal_type": "Employee",
            "action": 'Action::"configure"',
            "resource_type": "InternalSystem",
            "floor_path": os.path.join(REFS, "ops_admin_subnet_configure.cedar"),
        },
        {
            "name": "admin_emergency_access",
            "description": (
                "An admin Employee MUST be able to emergencyAccess an "
                "InternalSystem from any source IP"
            ),
            "type": "floor",
            "principal_type": "Employee",
            "action": 'Action::"emergencyAccess"',
            "resource_type": "InternalSystem",
            "floor_path": os.path.join(REFS, "admin_emergency_access.cedar"),
        },

        # -- Liveness -------------------------------------------------------
        {
            "name": "liveness_access",
            "description": "Employee+access+InternalSystem liveness",
            "type": "always-denies-liveness",
            "principal_type": "Employee",
            "action": 'Action::"access"',
            "resource_type": "InternalSystem",
        },
        {
            "name": "liveness_configure",
            "description": "Employee+configure+InternalSystem liveness",
            "type": "always-denies-liveness",
            "principal_type": "Employee",
            "action": 'Action::"configure"',
            "resource_type": "InternalSystem",
        },
        {
            "name": "liveness_emergency",
            "description": "Employee+emergencyAccess+InternalSystem liveness",
            "type": "always-denies-liveness",
            "principal_type": "Employee",
            "action": 'Action::"emergencyAccess"',
            "resource_type": "InternalSystem",
        },
    ]
