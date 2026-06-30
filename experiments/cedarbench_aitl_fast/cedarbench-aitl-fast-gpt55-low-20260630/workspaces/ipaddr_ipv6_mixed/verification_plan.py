"""Hand-authored verification plan for realworld/ipaddr_ipv6_mixed.

Tests Cedar's `ipaddr` extension with IPv6 + IPv4 dual-stack and the
family-discrimination predicates `.isIpv4()` / `.isIpv6()`.

The synthesizer must exercise:
  - `ip("...")` constructor with both IPv4 and IPv6 CIDRs,
  - `.isInRange(ip(...))` for CIDR containment,
  - `.isIpv4()` / `.isIpv6()` to discriminate address families,
  - `.isLoopback()` for the cross-family escape hatch on `connect`.

Two actions (`connect`, `manage`), each with one ceiling and two
family-specific floors (IPv4 + IPv6), plus per-action liveness:
  - 2 ceilings + 4 floors + 2 liveness checks = 8 total.
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # ── Safety ceilings ──────────────────────────────────────────────
        {
            "name": "connect_safety",
            "description": "connect permitted only when client is in IPv4 10.0.0.0/8 or IPv6 2001:db8::/48 AND server is loopback or same-family",
            "type": "implies",
            "principal_type": "Operator",
            "action": "Action::\"connect\"",
            "resource_type": "Server",
            "reference_path": os.path.join(REFS, "connect_safety.cedar"),
        },
        {
            "name": "manage_safety",
            "description": "manage permitted only when client is in family-appropriate admin subnet (10.20.0.0/24 or 2001:db8:1::/64)",
            "type": "implies",
            "principal_type": "Operator",
            "action": "Action::\"manage\"",
            "resource_type": "Server",
            "reference_path": os.path.join(REFS, "manage_safety.cedar"),
        },

        # ── Floors ───────────────────────────────────────────────────────
        {
            "name": "floor_connect_ipv4_corp",
            "description": "IPv4 corporate-range client MUST connect to IPv4 server",
            "type": "floor",
            "principal_type": "Operator",
            "action": "Action::\"connect\"",
            "resource_type": "Server",
            "floor_path": os.path.join(REFS, "floor_connect_ipv4_corp.cedar"),
        },
        {
            "name": "floor_connect_ipv6_corp",
            "description": "IPv6 corporate-range client MUST connect to IPv6 server",
            "type": "floor",
            "principal_type": "Operator",
            "action": "Action::\"connect\"",
            "resource_type": "Server",
            "floor_path": os.path.join(REFS, "floor_connect_ipv6_corp.cedar"),
        },
        {
            "name": "floor_manage_ipv4_admin",
            "description": "Client in IPv4 admin subnet 10.20.0.0/24 MUST manage any server",
            "type": "floor",
            "principal_type": "Operator",
            "action": "Action::\"manage\"",
            "resource_type": "Server",
            "floor_path": os.path.join(REFS, "floor_manage_ipv4_admin.cedar"),
        },
        {
            "name": "floor_manage_ipv6_admin",
            "description": "Client in IPv6 admin subnet 2001:db8:1::/64 MUST manage any server",
            "type": "floor",
            "principal_type": "Operator",
            "action": "Action::\"manage\"",
            "resource_type": "Server",
            "floor_path": os.path.join(REFS, "floor_manage_ipv6_admin.cedar"),
        },

        # ── Liveness ─────────────────────────────────────────────────────
        {
            "name": "liveness_connect",
            "description": "Operator+connect+Server liveness",
            "type": "always-denies-liveness",
            "principal_type": "Operator",
            "action": "Action::\"connect\"",
            "resource_type": "Server",
        },
        {
            "name": "liveness_manage",
            "description": "Operator+manage+Server liveness",
            "type": "always-denies-liveness",
            "principal_type": "Operator",
            "action": "Action::\"manage\"",
            "resource_type": "Server",
        },
    ]
