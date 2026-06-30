---
pattern: ip-address corporate network controls
difficulty: medium
features:
  - cedar ipaddr extension
  - cidr range membership
  - vpn segmentation
  - role-gated administrative subnet
domain: enterprise / network security
synthesis_difficulty: 3
---

# IP-Address Corporate Network -- Policy Specification

## Context

An enterprise access-control system gates access to internal corporate
systems by source IP address, role, and the sensitivity of the target
system. This is the first scenario in the benchmark exercising Cedar's
`ipaddr` extension (`ip("...")`, `.isInRange(...)`, `.isIpv4()`).

Entities:
- `Employee { role: String }` -- one of `"standard"`, `"ops"`, or
  `"admin"`.
- `InternalSystem { requiresVpn: Bool }` -- if `requiresVpn` is true
  the system can only be reached over the corporate VPN segment.

Context attribute `sourceIp: ipaddr` carries the source IP of the
request, populated by the host application (e.g. from the load
balancer's X-Forwarded-For after validation).

Three actions: `access` (read general systems), `configure` (mutate
system configuration), and `emergencyAccess` (admin-only break-glass
from any network).

## Network ranges

Corporate-allowed CIDR blocks (RFC1918):
- `10.0.0.0/8`
- `172.16.0.0/12`
- `192.168.0.0/16`

Special segments inside `10.0.0.0/8`:
- VPN segment: `10.10.0.0/16` -- where remote/VPN clients land.
- Admin subnet: `10.20.0.0/24` -- jump-host network for ops/admin.
- Compromised range: `10.50.0.0/16` -- a known-compromised subnet that
  must be excluded from ALL access decisions.

## Requirements

### 1. General Access (Permit)
- An `Employee` may perform `access` on an `InternalSystem` when ALL
  of the following hold:
  1. `context.sourceIp.isInRange(ip("10.0.0.0/8"))` OR
     `context.sourceIp.isInRange(ip("172.16.0.0/12"))` OR
     `context.sourceIp.isInRange(ip("192.168.0.0/16"))` -- i.e. the
     source IP sits inside one of the corporate blocks.
  2. `!context.sourceIp.isInRange(ip("10.50.0.0/16"))` -- the source
     IP is NOT in the compromised subnet.
  3. If `resource.requiresVpn` is true, additionally
     `context.sourceIp.isInRange(ip("10.10.0.0/16"))` -- VPN-required
     systems are reachable only from the VPN segment.

### 2. Configuration (Permit)
- Only an `Employee` whose `role` is `"ops"` or `"admin"` may perform
  `configure` on an `InternalSystem`, and only when the source IP
  sits in the admin subnet `10.20.0.0/24` AND the source IP is NOT in
  the compromised range `10.50.0.0/16`.
- Note: `10.20.0.0/24` and `10.50.0.0/16` do not overlap, but the
  ceiling still excludes the compromised range explicitly so the
  property holds independently of the network layout.

### 3. Emergency Access (Permit)
- An `Employee` whose `role` is `"admin"` may perform `emergencyAccess`
  on an `InternalSystem` from ANY source IP. This is the break-glass
  path used when normal network paths are unavailable. It does NOT
  exclude the compromised range -- by design, the break-glass path is
  always available to admins.
- Non-admin roles (`"standard"`, `"ops"`) may NEVER perform
  `emergencyAccess`.

## Notes
- `ip("...")` requires a string literal (the constructor is parsed at
  policy-load time).
- `.isInRange(ip("..."))` performs CIDR containment for both IPv4 and
  IPv6 addresses; it returns false when the address families differ.
- Cedar denies by default. The absence of a permit for `configure`
  outside the admin subnet, or for `emergencyAccess` by non-admins,
  is sufficient.
- The compromised-range exclusion (req 1.2) is a global safety
  property: every `access` floor in the verification plan repeats the
  exclusion (per CLAUDE.md §8.8 floor-bound consistency).
- Role values are exactly `"standard"`, `"ops"`, `"admin"`. No other
  roles exist.
