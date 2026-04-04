# Hotel Chain Permissions -- Policy Specification (with Franchise)

## Context

This policy governs access control for a hotel chain management platform with
Franchises, Hotels, Properties, Reservations, and Users.

The hierarchy is now 4 levels: Franchise -> Hotel -> Property -> Reservation.
Hotels belong to Franchises (via `Hotel in [Hotel, Franchise]`). Properties
belong to Hotels. Reservations belong to Properties.

Users have three permission tiers, each with a PermissionsMap now containing
`franchiseReservations: Set<Franchise>` in addition to hotel and property sets.
Users also have `franchiseAdminPermissions: Set<Franchise>`.

## Requirements

### 1. Viewer Permissions (Reservations)
- A user may **viewReservation** if the reservation is in
  `viewPermissions.franchiseReservations`, `viewPermissions.hotelReservations`,
  or `viewPermissions.propertyReservations`.
  (Franchise-level permissions cascade through Hotel to Property to Reservation.)

### 2. Member Permissions (Reservations)
- A user may **viewReservation**, **updateReservation**, or **createReservation**
  if the resource is in `memberPermissions.franchiseReservations`,
  `memberPermissions.hotelReservations`, or `memberPermissions.propertyReservations`.

### 3. Admin Permissions (Reservations)
- A user may perform all reservation actions including **grantAccessReservation**
  if the resource is in `franchiseAdminPermissions`, `hotelAdminPermissions`, or
  `propertyAdminPermissions`.

### 4. Viewer Permissions (Properties, Hotels & Franchises)
- A user may **viewProperty** if the resource is in any viewer permission set
  (franchise, hotel, or property level).
- A user may **viewHotel** if the resource is in franchise or hotel viewer sets.
- A user may **viewFranchise** if the franchise is in `viewPermissions.franchiseReservations`.

### 5. Member Permissions (Properties, Hotels & Franchises)
- Same cascade pattern: franchise-level member permissions cascade to hotels and properties.
- A user may **updateFranchise** with franchise-level member permissions.

### 6. Admin Permissions (Properties, Hotels & Franchises)
- Full admin permissions cascade: franchise admin covers all hotels and properties within.
- A user may **grantAccessFranchise** only with `franchiseAdminPermissions`.

## Notes
- The 4-level hierarchy means `resource in principal.franchiseAdminPermissions` covers
  all hotels, properties, and reservations within that franchise.
- Property-specific checks still require the `resource is Property` guard.
