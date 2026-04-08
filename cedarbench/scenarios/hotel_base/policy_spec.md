# Hotel Chains — Policy Specification

## Context

This policy governs access control for a hotel chain (called ABC) with
franchises and properties. Resources are organized in a hierarchy: a `Hotel`
represents a hotel chain or franchise (and chains can contain sub-chains),
a `Property` represents an individual hotel location belonging to a `Hotel`,
and resources like `Reservation` belong to a `Property`. The use case
includes only `Reservation` for now, but other resource types
(`PaymentDetails`, `Rates`, etc.) would extend the same pattern.

The system is role-based, with three roles: **viewer**, **member**
(editor), and **admin**. Roles are scoped per resource-type and per
hotel/property — for example, Alice may be a viewer of `Reservation`s at
a particular `Hotel` chain without having any access to `PaymentDetails`
at that chain. The admin role grants access to *all* resource types at
the hotel/property in question.

## Entity Model

- **User** is the only principal type. Each User has the following
  permissions stored as attributes:
  - `viewPermissions`, a `PermissionsMap` recording where the user is a
    viewer.
  - `memberPermissions`, a `PermissionsMap` recording where the user is a
    member (editor).
  - `hotelAdminPermissions`, a `Set<Hotel>` listing hotels where the user
    is an admin.
  - `propertyAdminPermissions`, a `Set<Property>` listing properties where
    the user is an admin.

  A `PermissionsMap` is a record with one set per resource type:
  - `hotelReservations: Set<Hotel>` — the set of `Hotel`s for which the
    user has the relevant role on `Reservation`s.
  - `propertyReservations: Set<Property>` — the set of `Property`s for
    which the user has the relevant role on `Reservation`s.

  (The schema is structured this way so that adding a new resource type,
  e.g. `PaymentDetails`, would add `hotelPaymentDetails`/`propertyPaymentDetails`
  fields without disturbing existing rules.)

- **Hotel** is a chain or franchise. A Hotel may be in another Hotel
  (`Hotel in [Hotel]`), expressing nested chains.
- **Property** represents an individual hotel location. A Property is in a
  Hotel (`Property in [Hotel]`).
- **Reservation** represents a guest reservation. A Reservation is in a
  Property (`Reservation in [Property]`).

## Requirements

### 1. Reservation Actions
Three actions apply to `Reservation`s: `viewReservation`,
`updateReservation`, and `grantAccessReservation`.

- **viewReservation** is permitted if the user has *view*, *member*, or
  *admin* role for reservations at the reservation's containing
  Property/Hotel. Concretely, the user is permitted to view a Reservation
  `r` if **any** of the following hold:
  - `r in principal.viewPermissions.propertyReservations`, OR
    `r in principal.viewPermissions.hotelReservations`
  - `r in principal.memberPermissions.propertyReservations`, OR
    `r in principal.memberPermissions.hotelReservations`
  - `r in principal.propertyAdminPermissions`, OR
    `r in principal.hotelAdminPermissions`

- **updateReservation** is permitted if the user has *member* or *admin*
  role for reservations at the reservation's containing Property/Hotel.
  Viewers cannot update.

- **grantAccessReservation** is permitted only if the user has *admin*
  role at the reservation's containing Property/Hotel. Viewers and
  members cannot grant access.

### 2. Property Actions
- **createReservation** on a Property is permitted if the user has *member*
  or *admin* role at that Property (or its containing Hotel chain) for
  reservations.

- **viewProperty** is permitted if the user has *view*, *member*, or *admin*
  role for **any** resource type at that Property or its containing Hotel
  chain. The intent (per the use-case writeup): a user who has any role for
  resources at a property/hotel inherits the corresponding role on the
  property/hotel itself, so that they may at least view it. With only
  `Reservation` as a resource type, this means: viewable if the user has
  any of the reservation roles (view, member, or admin) covering the
  property or its hotel.

- **updateProperty** is permitted if the user has *member* or *admin* role
  inheritance for the property — i.e., they are a *member* or *admin* on
  any resource type at that property or its hotel. With only Reservations,
  this means member or admin on reservations covering the property/hotel.

- **grantAccessProperty** is permitted only if the user has *admin* role
  inheritance — i.e., they are an admin at the property or its hotel.

### 3. Hotel Actions
- **createProperty** on a Hotel is permitted if the user has *member* or
  *admin* role inheritance at that Hotel.

- **createHotel** on a Hotel (creating a sub-chain) is permitted only if
  the user is an *admin* of the parent Hotel.

- **viewHotel** is permitted if the user has *view*, *member*, or *admin*
  role for any resource type at that hotel. Same inheritance rule as
  viewProperty.

- **updateHotel** is permitted if the user has *member* or *admin* role
  inheritance at the hotel.

- **grantAccessHotel** is permitted only if the user has *admin* role at
  the hotel.

### 4. Role Inheritance
- A user with role R for resources at a `Hotel` inherits role R for
  resources at every `Property` belonging to that `Hotel`. For
  reservations, this is naturally captured by checking `resource in
  principal.<role>Permissions.hotelReservations` because Reservations are
  transitively `in` their containing Hotel via Property.
- A user with admin role on a hotel/property has access to **all**
  resource types at that hotel/property, not just reservations. With only
  reservations defined here, the admin sets cover all reservation actions.
- A user with viewer or member role for any resource type at a
  hotel/property is allowed to *view* the hotel/property itself.

## Notes
- Cedar denies by default. The policies above grant the listed accesses;
  no explicit deny rules are needed.
- The schema uses two separate admin sets (`hotelAdminPermissions`,
  `propertyAdminPermissions`) rather than a unified `adminPermissions:
  Set<Hotel|Property>` because Cedar's type system at the time did not
  support entity unions in attribute types. The semantics are equivalent
  to a single set of admin scopes.
- Membership of a Reservation in its containing Property and Hotel is
  expressed via the entity hierarchy (`Reservation in Property in Hotel`),
  so `r in some_hotel` evaluates correctly via Cedar's transitive `in`.
