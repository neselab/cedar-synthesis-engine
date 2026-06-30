---
pattern: three-role separation of duties (SOX banking SoD)
difficulty: hard
features:
  - cross-step SoD via host-attested context attributes
  - optional context attributes with negated-has guards
  - role-based action assignment (trader / settlement_clerk / auditor / manager)
  - mutual exclusion across {trade, settle, audit} workflow
domain: finance / banking / SOX compliance
synthesis_difficulty: 4
---

# SOX Three-Role Separation of Duties — Policy Specification

## Context

This policy implements the classic SOX banking control: the trade
lifecycle is split across three independent roles — **trader**,
**settlement clerk**, and **auditor** — and **no single principal may
perform actions from more than one of those roles on the same trade**.
This is the canonical "trade / settle / confirm" SoD that Sarbanes-Oxley
§404 and most regulator guidance require for derivatives, FX, and
securities desks: the front-office trader who books a trade must not
also be the back-office clerk who settles it, and neither may also be
the auditor who signs off on it. A single principal able to perform any
two of those steps could push a fraudulent trade to completion
unilaterally.

Principal is `Employee`; resource is `Trade`. Employees have a `role`
attribute in `{"trader", "settlement_clerk", "auditor", "manager"}`.
There are three actions: `initiate_trade`, `settle_trade`,
`audit_trade`.

The SoD check is enforced via two host-supplied context attestations,
both **optional**:
- `prevTradeActor: Employee` — the employee who performed the prior
  `initiate_trade` step (set by the host application from the trade's
  audit trail; absent when no trade has been initiated yet).
- `prevSettleActor: Employee` — the employee who performed the prior
  `settle_trade` step (absent when settlement has not occurred yet).

The host application is responsible for populating these attributes
truthfully from its trade-state database before evaluating any
`settle_trade` or `audit_trade` request. The policy then enforces that
the current principal is not equal to either prior actor.

## Requirements

### 1. Initiate Trade (Trader or Manager, No SoD on Initiation)
- An employee with `role == "trader"` OR `role == "manager"` may
  `initiate_trade`. There is no SoD check on initiation because there
  are no prior workflow steps to be excluded from.
- Concretely: permit `initiate_trade` when
  `principal.role == "trader" || principal.role == "manager"`.

### 2. Settle Trade (Settlement Clerk or Manager, Not the Initiator)
- An employee with `role == "settlement_clerk"` OR `role == "manager"`
  may `settle_trade`, **provided they are not the same employee who
  initiated the trade**.
- The SoD check is: `principal != context.prevTradeActor`. Because
  `prevTradeActor` is OPTIONAL, the check must be has-guarded.
- If `prevTradeActor` is absent (host did not attest a prior actor),
  the SoD check is vacuously satisfied — the policy permits settlement
  on the assumption the host has already validated workflow ordering.
- Concretely: permit `settle_trade` when:
  - `principal.role == "settlement_clerk" || principal.role == "manager"`, AND
  - `(!(context has prevTradeActor) || (context has prevTradeActor && principal != context.prevTradeActor))`.

### 3. Audit Trade (Auditor Only, Neither Initiator nor Settler)
- An employee with `role == "auditor"` may `audit_trade`, **provided
  they are neither the prior trade actor nor the prior settlement
  actor**. Auditor is a hard role gate — managers may not audit.
- Both `prevTradeActor` and `prevSettleActor` must be has-guarded
  before comparison.
- Concretely: permit `audit_trade` when:
  - `principal.role == "auditor"`, AND
  - `(!(context has prevTradeActor) || (context has prevTradeActor && principal != context.prevTradeActor))`, AND
  - `(!(context has prevSettleActor) || (context has prevSettleActor && principal != context.prevSettleActor))`.

## Notes — Common Failure Modes

### §8.3 Negated-`has` trap (the key Cedar pitfall)
Cedar's type-checker does NOT propagate negation through `has`.
Writing the SoD check as:
```cedar
!(context has prevTradeActor) || principal != context.prevTradeActor
```
will be REJECTED by `cedar validate` because the right disjunct reads
`context.prevTradeActor` without a `has` guard on its own (the
type-checker treats each side of `||` independently). The correct
pattern is:
```cedar
(!(context has prevTradeActor) || (context has prevTradeActor && principal != context.prevTradeActor))
```
Both `prevTradeActor` and `prevSettleActor` need this treatment.

### Role-intersection consideration
Unlike §8.6, role here is a single `String` attribute (not a set of
group memberships), so an employee cannot simultaneously be both a
trader and an auditor in the same request — `role` is one value. The
SoD across the workflow comes from the cross-step principal-equality
checks, not from role intersection. Manager is the only role that
spans actions (initiate + settle), and even then the cross-step
SoD blocks them from settling their own trade.

### Why no SoD on initiation
There are no prior steps before initiation, so there is nothing to
exclude. The SoD constraint only meaningfully applies to settle and
audit, which depend on the prior workflow state.

### Vacuous-when-absent semantics
We deliberately make the SoD check vacuous when the host omits the
attestation. This matches the realistic deployment where the host
application is the source of truth for workflow ordering and the
policy enforces only the SoD predicate. Treating absence as "fail
closed" would force the host to always attest a prior actor even on
the first action of a trade, which is awkward and not what real
SOX-compliant systems do.
