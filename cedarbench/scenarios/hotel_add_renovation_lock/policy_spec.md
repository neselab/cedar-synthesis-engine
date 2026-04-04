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
### 7. Renovation Lock (Deny Rule with Admin Override)
- Property now has an `isUnderRenovation: Bool` attribute.
- If a property has `isUnderRenovation == true`, the **createReservation** action is
  **forbidden** on that property.
- **Exception**: Users with admin permissions for that property
  (`resource in principal.hotelAdminPermissions || resource in principal.propertyAdminPermissions`)
  bypass this restriction and may still create reservations on renovating properties.
- All other actions (viewProperty, updateProperty, grantAccessProperty, viewReservation, etc.)
  are unaffected by the renovation flag.

## Notes (Renovation Lock)
- The forbid rule must use an `unless` clause to allow admin override.
- The forbid applies to the `createReservation` action which targets Property resources.
