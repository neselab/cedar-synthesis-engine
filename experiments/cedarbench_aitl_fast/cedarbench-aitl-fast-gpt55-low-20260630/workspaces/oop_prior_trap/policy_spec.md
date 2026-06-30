---
pattern: OOP-prior trap — Java/C#-flavored entity names invite invalid Cedar idioms
difficulty: hard
features:
  - Set<String> membership via .contains()
  - String equality on enum-like status field
  - cross-entity field access (resource.accountHolder.userId)
  - integer comparison on Long balance
  - role-based gating
domain: enterprise banking / account management
synthesis_difficulty: 4
---

# OOP-Prior Trap — Policy Specification

## Context

The **AccountManager** class governs which **BankAccount** instances
its instances may operate on. Each AccountManager object holds an
`accountList` of user IDs corresponding to the customers in its book
of business. Each BankAccount has an `accountHolder` (a User), a
current `balance`, and an `accountStatus` flag.

This specification is phrased in deliberately object-oriented language
("call the manager's listed accounts," "verify the manager class,"
"check the account is open") to maximize the pull of an OOP prior on
the synthesizer. The synthesizer is expected to resist the prior and
emit valid Cedar — Cedar is NOT an OO language and the following
idioms are all invalid:

  - **Method calls on user-defined entities.** Cedar has no methods
    on user-defined types. Only extension types (`decimal`,
    `datetime`, `duration`, `ipaddr`) and `Set` expose method-style
    accessors. `principal.getAccount()`, `resource.isOpen()`,
    `account.balance.compareTo(0)` are all rejected.
  - **Null checks.** Cedar has no `null`. Required attributes always
    have a value; optional attributes are gated with `has`. Writing
    `resource.balance != null` is invalid syntax.
  - **`instanceof` / inheritance.** Cedar has no class hierarchy.
    Entity-type tests use the `is` keyword: `principal is AccountManager`.
    `principal instanceof AccountManager` is invalid.
  - **Chained method navigation.** Property access chains through
    fields only: `resource.accountHolder.userId`, never
    `resource.getAccountHolder().getUserId()`.

## Domain model

- **User** has `userId: String` (the identifier matched against
  `AccountManager.accountList`) and `employeeFlag: Bool` (informational).
- **AccountManager** has `roleType: String` (`"manager"` /
  `"associate"` / `"trainee"`) and `accountList: Set<String>` —
  a set of `User.userId` strings (NOT a set of User entity refs;
  this matters for Cedar's symbolic checker).
- **BankAccount** has `accountHolder: User`, `balance: Long`, and
  `accountStatus: String` (`"OPEN"` / `"FROZEN"` / `"CLOSED"`).
- **Actions:** `viewBalance`, `transferFunds`, `closeAccount`. No
  context attributes.

## Requirements

### 1. SAFETY CEILING — viewBalance
`viewBalance` is permitted ONLY when ALL of the following hold:
   - `principal.accountList.contains(resource.accountHolder.userId)`
     (the AccountManager's listed customers include this account's
     holder), AND
   - `resource.accountStatus != "CLOSED"` (the account is not closed).

Anything outside this conjunction MUST be denied. In particular,
no manager may view balances of closed accounts even if listed.

### 2. SAFETY CEILING — transferFunds
`transferFunds` is permitted ONLY when ALL of the following hold:
   - `principal.accountList.contains(resource.accountHolder.userId)`, AND
   - `resource.accountStatus == "OPEN"` (strict equality — frozen and
     closed accounts both forbid transfers), AND
   - `resource.balance > 0` (positive balance required; a zero or
     negative balance forbids transfer).

### 3. SAFETY CEILING — closeAccount
`closeAccount` is permitted ONLY when ALL of the following hold:
   - `principal.roleType == "manager"` (associate and trainee
     roleTypes are NEVER permitted to close), AND
   - `resource.balance == 0` (strict equality on Long; nonzero
     balances forbid closure regardless of sign).

   Note: the spec does NOT require `accountList.contains(...)` for
   `closeAccount` — managers may close any zero-balance account in
   the institution. The spec does not require status checks either.

### 4. FLOOR_VIEW_LISTED_OPEN — listed open accounts MUST be viewable
   - If `principal.accountList.contains(resource.accountHolder.userId)`
     AND `resource.accountStatus == "OPEN"`, `viewBalance` MUST be
     permitted.

### 5. FLOOR_VIEW_LISTED_FROZEN — listed frozen accounts MUST be viewable
   - If `principal.accountList.contains(resource.accountHolder.userId)`
     AND `resource.accountStatus == "FROZEN"`, `viewBalance` MUST be
     permitted. (Frozen accounts may be inspected for balance even
     though transfers are blocked.)

### 6. FLOOR_TRANSFER_LISTED_OPEN_POSITIVE — happy-path transfer MUST work
   - If `principal.accountList.contains(resource.accountHolder.userId)`
     AND `resource.accountStatus == "OPEN"` AND `resource.balance > 0`,
     `transferFunds` MUST be permitted.

### 7. FLOOR_CLOSE_MANAGER_ZERO — manager closing a zero-balance MUST work
   - If `principal.roleType == "manager"` AND `resource.balance == 0`,
     `closeAccount` MUST be permitted.

## Why the OOP prior is dangerous here (planner's note)

A naive synthesizer pulled by the OOP-flavored class names is likely
to emit invalid Cedar such as:

  - `principal.getAccountList().contains(...)` — there are no methods.
    Correct: `principal.accountList.contains(...)`.
  - `resource.accountHolder.getUserId()` — also methodless. Correct:
    `resource.accountHolder.userId`.
  - `resource.balance != null && resource.balance > 0` — Cedar has
    no null. Required Long attributes always have a value. Correct:
    `resource.balance > 0`.
  - `principal instanceof AccountManager` — instanceof does not exist.
    Correct: `principal is AccountManager`.
  - `resource.isOpen()` or `account.isClosed()` — methods do not exist
    on user-defined types. Correct: `resource.accountStatus == "OPEN"`,
    `resource.accountStatus != "CLOSED"`.
  - `principal.accountList.size() > 0` — `Set` does have
    `.contains()`, `.containsAll()`, `.containsAny()`, and
    `.isEmpty()`, but NOT `.size()`. Use `.isEmpty()` if needed.

The intended converged candidate is three small `permit` policies
(one per action), each of which is a straight conjunction of
attribute reads matching the ceiling above. No global forbids are
needed.

## Non-requirements

- `User.employeeFlag` is informational and does not appear in any
  rule.
- The accountList is keyed by `User.userId` strings, NOT by `User`
  entity references. A naive translation to
  `principal.accountList.contains(resource.accountHolder)` would be a
  type error — `accountList: Set<String>` cannot contain a User
  entity.
- `closeAccount` deliberately does NOT require `accountList`
  membership — this asymmetry exists to discourage rote copy-paste
  of the viewBalance condition.
