---
pattern: schema common type definitions shared across entities
difficulty: medium
features:
  - schema common type definitions (`type X = ...`)
  - nested record alias (`ContactInfo` contains `Address`)
  - common type reused across multiple entity types
  - 3-deep nested record access (`resource.contact.address.country`)
  - mixed principal types (Customer, Vendor, Employee, Admin) per action
domain: customer relationship management / contact directory
synthesis_difficulty: 3
---

# Common Type Definitions — Contact Directory

## Context

A contact directory holds three kinds of party records — `Customer`,
`Vendor`, and `Employee` — that all share the same shape of contact
information. The schema factors this shape into two **common type
definitions**:

```
type Address     = { street: String, zip: String, country: String };
type ContactInfo = { email: String, phone: String, address: Address };
```

Each entity attaches a `contact: ContactInfo` plus its own
type-specific fields (`kycStatus`, `taxId`, `dept`). A separate `Admin`
entity has no attributes and acts purely as a privileged principal.

The point of this scenario is to test the synthesizer's handling of:
- **Common type aliases** in the schema. The synthesizer must reach
  the `country` field through the alias chain
  `resource.contact.address.country` — not flatten it into something
  like `resource.address.country`.
- **Mixed principal types per action.** `viewContact` accepts four
  principal types (the three party types plus `Admin`); `updateContact`
  accepts only the three party types; `verifyAddress` accepts only
  `Admin`.

## Requirements

### Action: viewContact

Permitted when ANY of the following hold:

1. The principal is the resource itself (`principal == resource`),
   meaning the party is viewing their own contact record.
2. The principal is an `Admin`. Admins have unconditional read across
   all party records.

Floors:
- A `Customer` MUST be permitted to view their own contact.
- An `Employee` MUST be permitted to view their own contact.
- An `Admin` MUST be permitted to view any `Customer`'s contact.

### Action: updateContact

Permitted ONLY when `principal == resource` (the party updates their
own record). There is **no admin override** on update — admins can
read but cannot edit.

Floor:
- A `Customer` MUST be permitted to update their own contact.

### Action: verifyAddress

Permitted ONLY when both:
- The principal is an `Admin`, AND
- `resource.contact.address.country == "US"` (domestic addresses only).

Floor:
- An `Admin` MUST be permitted to verify a `Customer` whose address
  country is `"US"`.

### Liveness

Each of the three actions must permit at least one request.

## Out of scope

- No temporal constraints.
- No role hierarchy beyond `Admin` vs party.
- No cross-party visibility (e.g. a Vendor seeing a Customer's contact
  is denied unless that Vendor is also somehow the Customer, which the
  schema forbids by typing).
- No global forbids (so floors do not need exclusion clauses per §8.8).
