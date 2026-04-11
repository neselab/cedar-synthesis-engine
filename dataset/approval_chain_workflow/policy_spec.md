# Approval Chain Workflow — Policy Specification

## Context

This policy governs a compliance/legal document approval workflow. A
Document transitions through states `"draft"` → `"in_review"` →
`"approved"` or `"rejected"`, and transitions are gated on the set of
required approvers having signed off.

Principal is `User`; resource is `Document`. There are five actions:
`submit`, `approve`, `finalize`, `reject`, and `read`.

## Entity Model

- **User**: the principal. Represents any user in the system.
- **Document**: the resource. Each Document has:
  - `owner: User` — the document's creator.
  - `requiredApprovers: Set<User>` — the exact set of users whose
    approval is required before the document can be finalized. This set
    is set at document-creation time and does not change.
  - `currentApprovals: Set<User>` — the set of users who have signed off
    so far. This set grows monotonically as approvals come in.
  - `status: String` — one of `"draft"`, `"in_review"`, `"approved"`,
    `"rejected"`.

## Requirements

### 1. Submit (Draft → In Review)
- The document **owner** may submit the document for review. This
  transitions the status from `"draft"` to `"in_review"`.
- Concretely: permit `submit` when `principal == resource.owner` AND
  `resource.status == "draft"`.
- Only the owner may submit. No other user, including required
  approvers, may perform this action.

### 2. Approve (Record Approval)
- A user may `approve` a document if they are a member of the
  document's `requiredApprovers` set AND the document is currently
  `"in_review"`. Concretely: permit `approve` when `principal in
  resource.requiredApprovers` AND `resource.status == "in_review"`.
- The approve action records the user in `currentApprovals`; the
  policy does not enforce monotonicity (the host application handles
  set-addition).
- Users who are not in the required-approvers set cannot approve,
  regardless of any other role.

### 3. Finalize (In Review → Approved)
- Any user in the required-approvers set may `finalize` the document,
  transitioning the status to `"approved"`, provided ALL required
  approvers have already signed off:
  `resource.currentApprovals.containsAll(resource.requiredApprovers)`.
- Concretely: permit `finalize` when all THREE of:
  - `principal in resource.requiredApprovers`, AND
  - `resource.status == "in_review"`, AND
  - `resource.currentApprovals.containsAll(resource.requiredApprovers)`.
- The `containsAll` check is the core requirement — a document cannot
  be finalized until every required approver has signed off.

### 4. Reject (In Review → Rejected)
- Any user in the required-approvers set may `reject` a document during
  review, regardless of whether others have approved. A single rejection
  is sufficient to block finalization.
- Concretely: permit `reject` when `principal in
  resource.requiredApprovers` AND `resource.status == "in_review"`.

### 5. Read (Any Time)
- The document's owner may always `read` the document regardless of
  state. Required approvers may always `read`. Other users may NOT
  read the document.
- Concretely: permit `read` when either `principal == resource.owner`
  OR `principal in resource.requiredApprovers`.

### 6. No Write Actions on Terminal States (Forbid)
- Once a document is in `"approved"` or `"rejected"` state, no further
  `submit`, `approve`, `finalize`, or `reject` actions may be performed
  on it. The terminal states are immutable.
- Concretely: **forbid** `submit`, `approve`, `finalize`, `reject` when
  `resource.status == "approved"` OR `resource.status == "rejected"`.
- Reading terminal-state documents is still allowed per §5.

## Notes
- The `containsAll` requirement on finalize is the central safety
  property. Any candidate policy that permits finalize without it is
  incorrect.
- The reject-from-any-approver rule means a single negative vote
  blocks the document; this models a "unanimous consent" workflow.
- The terminal-state forbid should override all four action permits
  (submit, approve, finalize, reject). Read is unaffected.
- Cedar denies by default; the terminal-state forbid is an explicit
  override on top of the permit rules.
