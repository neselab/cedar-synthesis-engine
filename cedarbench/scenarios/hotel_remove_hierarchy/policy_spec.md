# Hotel Chain Permissions -- Policy Specification (Flat Hierarchy)

## Context

This policy governs access control for a hotel chain management platform with
Hotels, Properties, Reservations, and Users.

Properties are now **standalone entities** -- they do NOT belong to Hotels via
the entity hierarchy. Hotels can still contain other Hotels (sub-brands).
Reservations still belong to Properties.

Users have the same three permission tiers as before.

## Requirements

### 1. Viewer Permissions (Reservations)
- A user may **viewReservation** if the reservation's property is in
  the user's `viewPermissions.propertyReservations`.
- Hotel-level viewer permissions (`viewPermissions.hotelReservations`) still
  apply but NO LONGER cascade to properties since Property is not in Hotel.

### 2. Member Permissions (Reservations)
- A user may **viewReservation**, **updateReservation**, or **createReservation**
  if the resource is in the user's `memberPermissions.propertyReservations`.
- Hotel-level member permissions still apply but do not cascade to properties.

### 3. Admin Permissions (Reservations)
- A user may **viewReservation**, **updateReservation**, **createReservation**, and
  **grantAccessReservation** if the resource is in the user's `propertyAdminPermissions`.
- Hotel-level admin permissions still apply but do not cascade to properties.

### 4. Viewer Permissions (Properties & Hotels)
- A user may **viewProperty** if the property is in `viewPermissions.propertyReservations`.
- A user may **viewHotel** if the hotel is in `viewPermissions.hotelReservations`.
- Hotel viewer permissions do NOT grant property viewing since Property is no longer in Hotel.

### 5. Member Permissions (Properties & Hotels)
- Same pattern: property-level and hotel-level permissions are checked independently.
  Hotel membership no longer cascades to properties.

### 6. Admin Permissions (Properties & Hotels)
- Same pattern: `hotelAdminPermissions` only covers Hotels, `propertyAdminPermissions`
  only covers Properties. No cascade between the two.

## Notes
- The key difference from the base scenario: `Property` has no `in [Hotel]` clause.
- Permissions that relied on hotel-level sets cascading to property-level resources
  through the hierarchy will no longer work. Each level must be granted independently.
