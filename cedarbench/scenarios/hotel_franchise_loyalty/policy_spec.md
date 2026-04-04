# Hotel Chain Permissions -- Policy Specification (Franchise + Loyalty + Renovation)

## Context

This policy governs access control for a hotel chain management platform with
Franchises, Hotels, Properties, Reservations, and Users.

The hierarchy is 4 levels: Franchise -> Hotel -> Property -> Reservation.
Hotels belong to Franchises (via `Hotel in [Hotel, Franchise]`). Properties
belong to Hotels. Reservations belong to Properties.

Users have three permission tiers with PermissionsMaps containing franchise,
hotel, and property sets. Users also have a `loyaltyTier: Long` (1-5).
Properties have `isUnderRenovation: Bool` and `isPremium: Bool`.

## Requirements

### 1. Viewer Permissions (Reservations)
- A user may **viewReservation** if the reservation is in
  `viewPermissions.franchiseReservations`, `viewPermissions.hotelReservations`,
  or `viewPermissions.propertyReservations`.

### 2. Member Permissions (Reservations)
- A user may **viewReservation**, **updateReservation**, or **createReservation**
  if the resource is in `memberPermissions.franchiseReservations`,
  `memberPermissions.hotelReservations`, or `memberPermissions.propertyReservations`.

### 3. Admin Permissions (Reservations)
- A user may perform all reservation actions including **grantAccessReservation**
  if the resource is in `franchiseAdminPermissions`, `hotelAdminPermissions`,
  or `propertyAdminPermissions`.

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

### 7. Renovation Lock (Deny Rule with Admin Override)
- If a property has `isUnderRenovation == true`, the **createReservation** action is
  **forbidden** on that property.
- **Exception**: Users with admin permissions for that property
  (`resource in principal.franchiseAdminPermissions || resource in principal.hotelAdminPermissions || resource in principal.propertyAdminPermissions`)
  bypass this restriction and may still create reservations.

### 8. Loyalty Tier Restriction (Deny Rule)
- If a property has `isPremium == true`, the **createReservation** action is
  **forbidden** unless the user's `loyaltyTier >= 3`.
- This applies to ALL users including admins -- the loyalty tier check has no admin bypass.

## Notes
- Two independent forbid rules apply to **createReservation**: renovation lock (with admin
  override) and loyalty tier (no override). Both must pass for the action to be allowed.
- The 4-level hierarchy means franchise-level permissions cascade through hotels to properties.
- This is a complex scenario with 3 permission tiers, 4 entity hierarchy levels, and 2 forbid rules.
