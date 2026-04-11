# Tax Preparer — Policy Specification

## Context

This policy governs access control for an organization that prepares
taxes for its clients. Tax-preparing **Professionals** access **Document**s
owned by **Client**s in order to do tax work. Access is granted only
when **two** independent conditions are met simultaneously:

1. The Professional has been granted access to the Document — either
   structurally (because they are part of an organization whose
   service line and other features match the Document's) or via an
   ad-hoc grant added on the side.
2. The Client who owns the Document has given consent for Professionals
   in the requesting Professional's location ("team region") to view
   their documents. The consent is supplied per-request via the
   authorization context, scoped to a specific list of locations.

Both conditions are conjunctive — failing either denies access. The
consent rule is expressed as a `forbid` so that any future ad-hoc
permits added by other operators are still constrained by it.

This scenario is in the `Taxpreparer` namespace.

## Entity Model

- **Professional** (`Taxpreparer::Professional`) is the principal
  type. Each Professional has:
  - `assigned_orgs: Set<orgInfo>` where each `orgInfo` is a record
    `{ organization: String, serviceline: String, location: String }`.
    A professional may belong to multiple (organization, serviceline,
    location) assignments.
  - `location: String` — the professional's primary work location
    (their team region), used for consent checking.
- **Client** (`Taxpreparer::Client`) is the owner of Documents. Each
  Client has:
  - `organization: String` — the organization the client is contracting
    with.
- **Document** (`Taxpreparer::Document`) is the protected resource.
  Each Document has:
  - `serviceline: String` — the service line the work falls under.
  - `location: String` — the location associated with the document.
  - `owner: Client` — the client who owns the document.
- **Consent** is a record type passed in the request context (not an
  entity). It carries:
  - `client: Client` — the client who issued the consent.
  - `team_region_list: Set<String>` — the list of professional locations
    (team regions) for which the client has consented to access.

## Action

- **viewDocument** is the only action. It applies to `principal:
  Professional, resource: Document, context: { consent: Consent }`.

## Requirements

### 1. Org-Match Permit (Static Rule)
A Professional may **viewDocument** on a Document if there exists an
assignment in `principal.assigned_orgs` such that all three of the
following match the Document and its owner:

- The assignment's `organization` matches the Document owner's
  `organization` (i.e., `principal.assigned_orgs.contains(o)` for some
  `o` where `o.organization == resource.owner.organization`).
- The assignment's `serviceline` matches `resource.serviceline`.
- The assignment's `location` matches `resource.location`.

In other words, the Professional must be assigned to an
(organization, serviceline, location) triple that lines up with the
Document and its owning client. This is the structural / organizational
access path.

### 2. Ad-Hoc Permit (Template-Linked Rule)
The system supports adding ad-hoc grants of viewDocument access on a
per-(professional, document) basis via Cedar template links. Each
ad-hoc grant is a separate permit policy of the form

```
permit (principal == ?principal, action == Action::"viewDocument",
        resource == ?resource);
```

linked at runtime with the specific Professional and Document. These
ad-hoc grants are not part of the base policy file and are added or
removed by the host application as needed. The base policy must be
compatible with such grants existing alongside it — see §3 below.

### 3. Consent Forbid
The Client must have given consent before any Professional may view
their document. This is enforced as a **forbid** rule so that it
overrides every permit, including the static org-match permit and any
ad-hoc template-linked permits:

- **Forbid** `viewDocument` whenever the consent supplied in the
  request context is not valid for this access. Concretely, the forbid
  fires when **either**:
  - `context.consent.client != resource.owner` (the consent in the
    request is for a different client than the Document's owner — the
    consent does not authorize access to this document), OR
  - `!context.consent.team_region_list.contains(principal.location)`
    (the requesting professional's location is not in the list of
    team regions the client has consented to).
- The forbid has no exceptions. There is no `unless` clause; any
  request lacking valid consent is denied regardless of organizational
  match or ad-hoc grant.

### 4. Permit Composition
- A request is permitted only if **at least one** permit rule (§1 or
  §2) fires AND the consent forbid (§3) does NOT fire.
- A request that satisfies the org match (§1) but lacks valid consent
  is denied. A request that has valid consent but no permit (neither
  org match nor ad-hoc grant) is also denied. Both are required.

## Notes
- Cedar denies by default. The two permits in §1 and §2 grant the
  listed accesses; the forbid in §3 overrides them when consent is
  missing or mismatched.
- The consent rule is intentionally a `forbid` rather than an
  additional `when` clause on each permit. This way, future ad-hoc
  permits added by template linking inherit the consent constraint
  automatically without needing to be modified.
- The `assigned_orgs` set may contain multiple records with different
  service lines, locations, and organizations. The org-match rule
  succeeds if **any** record in the set matches; this is naturally
  expressed in Cedar with set-iteration / containment idioms.
- Schema namespace is `Taxpreparer`; entity type names in policies
  must be qualified accordingly.
