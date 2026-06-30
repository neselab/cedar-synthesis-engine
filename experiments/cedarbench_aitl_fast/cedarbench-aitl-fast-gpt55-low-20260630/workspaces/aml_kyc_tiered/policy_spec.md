---
pattern: AML risk-based tiered KYC / Customer Due Diligence
difficulty: hard
features:
  - tiered verification thresholds
  - amount-band conditioning
  - risk-score branching
  - multi-attribute attestation conjunction
domain: financial / compliance
synthesis_difficulty: 3
---

# AML / KYC Tiered Customer Due Diligence — Policy Specification

## Context

This policy implements an **AML risk-based tiered Customer Due Diligence
(CDD)** scheme for a retail bank, modelled on FATF Recommendation 10 and
the EU 6th AML Directive. Customer accounts are stratified into three
KYC tiers — Simplified Due Diligence (`SDD`), Customer Due Diligence
(`CDD`), and Enhanced Due Diligence (`EDD`) — based on the bank's risk
assessment. Each customer-facing action requires a different verification
depth depending on transaction size and the customer's risk profile.

Principals are `BankCustomer` entities with risk score, KYC tier, and
EDD attestations. Resources are either the customer's account itself
(via `viewAccount` / `escalateReview`), a `Transaction` (via
`transferOut`), or the bank's product catalog (via `openProduct`).

## Entities

- **BankCustomer** — the principal.
  - `riskScore: Long` — 0 (lowest) to 100 (highest), as scored by the
    bank's risk engine.
  - `kycTier: String` — one of `"SDD"`, `"CDD"`, `"EDD"`.
  - `uboVerified: Bool` — Ultimate Beneficial Owner verification
    completed (mandatory for high-value transactions).
  - `adverseMediaClean: Bool` — adverse media / sanctions screening
    returned no hits.
- **Transaction** — the outbound transfer being attempted.
  - `amount: Long` — transaction amount in the bank's reporting currency.
  - `requiresEdd: Bool` — pre-flagged by the transaction monitoring
    system as triggering an EDD condition (e.g. cross-border to a
    higher-risk jurisdiction).

## Actions

| Action            | Resource type | Description                              |
|-------------------|---------------|------------------------------------------|
| `viewAccount`     | BankCustomer  | View own account summary / balance.      |
| `transferOut`     | Transaction   | Initiate an outbound transfer.           |
| `openProduct`     | BankCustomer  | Open a new product (loan, brokerage…).   |
| `escalateReview`  | BankCustomer  | File a manual compliance escalation.     |

## Access rules

### 1. `viewAccount`

Any KYC tier (`SDD`, `CDD`, or `EDD`) may view their own account. Basic
identity verification is the only requirement and is satisfied by being
in any tier.

### 2. `transferOut`

Verification depth scales with transaction size:

| Amount band            | Required tier(s)                                       |
|------------------------|--------------------------------------------------------|
| `amount < 10000`       | `SDD`, `CDD`, or `EDD`                                 |
| `10000 ≤ amount ≤ 100000` | `CDD` or `EDD`                                       |
| `amount > 100000`      | `EDD` AND `uboVerified` AND `adverseMediaClean`        |

### 3. `openProduct`

Two paths:

- **High-risk customer or EDD-flagged product:** if `riskScore > 70` OR
  `resource.requiresEdd`, the customer MUST be `EDD` AND have both
  `uboVerified` and `adverseMediaClean`.
- **Standard:** otherwise, `CDD` or `EDD` is sufficient. (`SDD`
  customers may not open new products even at low risk — opening a new
  product always elevates the relationship beyond simplified diligence.)

Note: `resource` for `openProduct` is the `BankCustomer` themselves
(they are opening a product associated with their own profile). The
`requiresEdd` attribute on the resource is therefore checked via the
transaction-flag analogue stored on `BankCustomer` — see schema (we use
`resource.uboVerified` etc. and the high-risk decision is computed from
the customer's own attributes, not from a Transaction). To keep the
contract clear, the high-risk branch is predicated on
`principal.riskScore > 70` (the principal IS the resource here).

### 4. `escalateReview`

Any compliance-aware tier (`CDD` or `EDD`) may file an escalation.
`SDD` customers cannot — by definition they have not been onboarded
through compliance-aware channels.

## Notes

- Per §8.6, the SDD-blocked-from-large-transfers rule is encoded as a
  **positive permit at each tier-amount combination**, not as a forbid
  on `kycTier == "SDD"`. A customer cannot simultaneously hold two
  tiers, but the same principle applies to keep the property
  composable with future role-extensions.
- Per §8.8, every floor below respects the EDD requirements for
  high-amount transfers (no floor permits a `transferOut` with
  `amount > 100000` unless EDD + UBO + adverseMediaClean all hold).
- The `requiresEdd` attribute on Transaction triggers EDD escalation
  for outbound transfers — but `transferOut` is already gated by
  amount bands, so `requiresEdd` is not separately checked there. It
  is included in the schema for future extension and to test whether
  the synthesizer hallucinates a constraint from it.
- Common failure modes: (a) using `forbid` on SDD instead of positive
  permits per band, (b) forgetting `uboVerified` AND `adverseMediaClean`
  on the high-amount transferOut, (c) permitting SDD to open products,
  (d) permitting SDD to escalate.
