---
pattern: causal predecessor chain (sequential workflow attestation)
difficulty: medium
features:
  - optional record context attribute
  - has-guarded reads on optional record
  - sequential workflow / state machine via attestation
  - separation of duties (predecessor.actor != principal)
  - string equality on actionType
domain: workflow / compliance
synthesis_difficulty: 3
---

# Causal Predecessor Chain — Policy Specification

## Context

This policy governs a three-step sequential workflow on `Document`
resources:

```
prepare ──▶ submit ──▶ approve
```

Each later action requires *attested causal evidence* that its
immediate predecessor already succeeded. The host application is the
source of truth for the workflow log; before evaluating a request it
looks up the most recent successful action on the document and, if
relevant, attaches an attestation record to the request context as
the optional `predecessorAuthorized` attribute. The policy reads that
attestation and enforces the chain.

This pattern shows up in real production systems whenever a step's
authorization depends on a fact about prior history (e.g. "you can
only sign once you've reviewed", "you can only release once QA
acknowledged", "you can only approve once submitted"). Encoding the
predecessor as host-supplied context keeps the policy stateless while
still expressing the causal dependency.

Principal is `User`; resource is `Document`. There are three actions:
`prepare`, `submit`, `approve`.

## Entity Model

- **User** — the principal. Any user in the system.
- **Document** — the resource. Has no required attributes for this
  policy; the workflow state lives in the host application's log and
  is surfaced via context, not on the document itself.

## Context

All three actions accept an optional record:

```
predecessorAuthorized?: {
    actor: User,
    actionType: String,
    timestamp: datetime,
}
```

Semantics: when present, it certifies that the host application has
verified that user `actor` successfully performed `actionType` on this
document at `timestamp`. When absent, no predecessor has been
verified.

Because the attribute is optional, every read MUST be `has`-guarded
(see §8.3 in `docs/harness_fix_log.md`).

## Requirements

### 1. Prepare (Step 1 — root of the chain)
- Any user may `prepare` a document. There is no predecessor for the
  first step.
- Concretely: permit `prepare` for any `principal` on any `resource`
  with no further conditions.
- The presence or absence of `predecessorAuthorized` is irrelevant
  to `prepare`.

### 2. Submit (Step 2 — requires Prepare)
- A user may `submit` a document only if the host has attached a
  `predecessorAuthorized` attestation AND the attested action was
  `"prepare"`.
- Concretely: permit `submit` when:
  - `context has predecessorAuthorized`, AND
  - `context.predecessorAuthorized.actionType == "prepare"`.
- The actor of the predecessor is unconstrained for `submit` — the
  same user who prepared may also submit.

### 3. Approve (Step 3 — requires Submit + separation of duties)
- A user may `approve` a document only if the host has attached a
  `predecessorAuthorized` attestation AND the attested action was
  `"submit"` AND the actor who submitted is NOT the principal who is
  now trying to approve.
- Concretely: permit `approve` when:
  - `context has predecessorAuthorized`, AND
  - `context.predecessorAuthorized.actionType == "submit"`, AND
  - `context.predecessorAuthorized.actor != principal`.
- This enforces separation of duties: the user who submitted a
  document cannot also approve it.

### 4. Default Deny
- Cedar denies by default. There are no `forbid` rules in this
  policy; the chain is enforced positively by the `permit` rules
  themselves.

## Notes
- The host application is trusted to populate `predecessorAuthorized`
  truthfully. The policy does not (and cannot) verify the timestamp
  or that the attested action actually occurred — that is the host's
  job.
- A candidate that permits `submit` without a predecessor is wrong.
- A candidate that permits `approve` when the predecessor is a
  `"prepare"` (skipping `submit`) is wrong.
- A candidate that permits `approve` when the predecessor's actor
  equals the principal violates separation of duties and is wrong.
- Per §8.3 of `docs/harness_fix_log.md`: every read of
  `context.predecessorAuthorized.<field>` MUST be guarded by
  `context has predecessorAuthorized`. Do not write naked
  `!(context has predecessorAuthorized) || context.predecessorAuthorized.x == ...`
  — Cedar's typechecker rejects it.
