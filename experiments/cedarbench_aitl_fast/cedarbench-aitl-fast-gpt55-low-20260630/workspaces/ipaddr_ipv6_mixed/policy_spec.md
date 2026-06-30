---
pattern: dual-stack network ACL via Cedar ipaddr extension
difficulty: medium
features:
  - ipaddr extension (ip() constructor with CIDR)
  - IPv6 + IPv4 dual-stack address handling
  - .isIpv4() / .isIpv6() family discrimination
  - .isInRange() CIDR containment
  - .isLoopback() classification
domain: data center / network access control
synthesis_difficulty: 3
---

# Dual-Stack Data Center Access — Policy Specification

## Context

This policy controls operator access to data-center servers in a
dual-stack (IPv4 + IPv6) network. It exercises Cedar's `ipaddr`
extension type, including the family-discrimination predicates
(`.isIpv4()`, `.isIpv6()`), CIDR containment (`.isInRange()`), and
the `.isLoopback()` classification.

Principal is `Operator`. Resource is `Server` with attribute
`serverIp: ipaddr`. The request `context` carries `clientIp: ipaddr`
(the IP address the operator is connecting from). Two actions:
`connect`, `manage`.

## Requirements

### 1. Connect (Family-Aware Corporate Range)

An `Operator` may `connect` to a `Server` when **both** of the
following hold:

- **Client is in a corporate range.** The `context.clientIp` lies
  in the IPv4 corporate range `10.0.0.0/8` **OR** in the IPv6
  corporate range `2001:db8::/48`.

- **Server reachability check.** The `resource.serverIp` is the
  loopback address (any family), **OR** the server's IP belongs to
  the same address family as the client (IPv4-to-IPv4 or
  IPv6-to-IPv6 — no cross-family connections).

### 2. Manage (Admin Subnet, Family-Discriminated)

An `Operator` may `manage` a `Server` when the `context.clientIp`
is in the appropriate admin subnet for its family:

- If `context.clientIp.isIpv4()`, then it must lie in `10.20.0.0/24`.
- If `context.clientIp.isIpv6()`, then it must lie in `2001:db8:1::/64`.

The intent is that you must use `.isIpv4()` / `.isIpv6()` to
discriminate which CIDR test to apply — calling `.isInRange()` with
an IPv4 CIDR on an IPv6 address (or vice versa) returns false, but
the policy should clearly express the family-aware rule.

`manage` does not separately constrain `resource.serverIp` — admin
subnet membership of the client is sufficient.

## Notes

- Cedar's `ipaddr` extension provides:
  `ip("...")` constructor (accepts plain IP or CIDR notation, both
  IPv4 and IPv6); `.isIpv4()`, `.isIpv6()`, `.isLoopback()`,
  `.isMulticast()` predicates; and `.isInRange(other)` for CIDR
  containment.
- `2001:db8::/48` is IANA's documentation prefix; `10.0.0.0/8` is
  RFC 1918 private space.
- Cross-family `.isInRange()` calls return false (an IPv4 address
  is never "in range" of an IPv6 CIDR), but explicit family checks
  make intent clear and avoid relying on that semantic.
