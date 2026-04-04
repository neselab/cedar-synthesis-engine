# Hotel Chain Permissions -- Policy Specification

## Context

This policy governs access control for a hotel chain management platform with
Hotels, Properties, Reservations, and Users.

Hotels can contain other Hotels (sub-brands) and Properties. Properties belong
to Hotels. Reservations belong to Properties. This creates a 3-level hierarchy:
Hotel -> Property -> Reservation.

Users have three permission tiers, each represented by a PermissionsMap containing
Sets of Hotels and Properties:
- **viewPermissions**: read-only access
- **memberPermissions**: read + write access
- **hotelAdminPermissions** / **propertyAdminPermissions**: full admin access

PermissionsMap is a record with `hotelReservations: Set<Hotel>` and
`propertyReservations: Set<Property>`.

## Requirements

### 1. Viewer Permissions (Reservations)
- A user may **viewReservation** if the reservation's property (or hotel) is in
  the user's `viewPermissions.hotelReservations` or `viewPermissions.propertyReservations`.

### 2. Member Permissions (Reservations)
- A user may **viewReservation**, **updateReservation**, or **createReservation**
  if the resource is in the user's `memberPermissions.hotelReservations` or
  `memberPermissions.propertyReservations`.

### 3. Admin Permissions (Reservations)
- A user may **viewReservation**, **updateReservation**, **createReservation**, and
  **grantAccessReservation** if the resource is in the user's `hotelAdminPermissions`
  or `propertyAdminPermissions`.

### 4. Viewer Permissions (Properties & Hotels)
- A user may **viewProperty** or **viewHotel** if the resource is in the user's
  `viewPermissions.hotelReservations`, or (for Properties only) in
  `viewPermissions.propertyReservations`.

### 5. Member Permissions (Properties & Hotels)
- A user may **viewProperty**, **updateProperty**, **createProperty**, **viewHotel**,
  **updateHotel**, **createHotel** if the resource is in the user's
  `memberPermissions.hotelReservations`, or (for Properties only) in
  `memberPermissions.propertyReservations`.

### 6. Admin Permissions (Properties & Hotels)
- A user may perform all property/hotel actions including **grantAccessProperty**
  and **grantAccessHotel** if the resource is in the user's `hotelAdminPermissions`,
  or (for Properties only) in `propertyAdminPermissions`.

## Notes
- Hierarchy membership is checked via `resource in principal.<permissions>.<set>`.
- Properties use an additional `resource is Property` guard before checking
  property-specific permission sets.
- Cedar denies by default; no explicit deny-by-default rule is needed.
### 7. Seasonal Rate Viewing
- Property now has `seasonStart: Long` and `seasonEnd: Long` attributes,
  representing epoch timestamps marking the active season window.
- A new **viewRates** action is available on Properties. It requires a context
  attribute `currentTime: Long` representing the current epoch timestamp.
- A user may **viewRates** on a property only if:
  1. The user has at least viewer permissions for the property
     (`resource in principal.viewPermissions.hotelReservations` or
      `resource in principal.viewPermissions.propertyReservations` -- or higher tier), AND
  2. The current time falls within the season window:
     `context.currentTime >= resource.seasonStart && context.currentTime <= resource.seasonEnd`.
- Outside the season window, **viewRates** is forbidden for all non-admin users.
- Admin users (`resource in principal.hotelAdminPermissions || resource in principal.propertyAdminPermissions`)
  may **viewRates** at any time regardless of the season window.

## Notes (Temporal Rates)
- The season window check uses numeric comparison on Long values representing timestamps.
- The forbid rule for out-of-season viewing uses: `context.currentTime < resource.seasonStart || context.currentTime > resource.seasonEnd`.
- Admin override on the temporal restriction uses an `unless` clause on the forbid.
