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
### 7. Loyalty Tier Restriction (Deny Rule)
- User now has a `loyaltyTier: Long` attribute (values 1 through 5).
- Property now has an `isPremium: Bool` attribute.
- If a property has `isPremium == true`, the **createReservation** action is
  **forbidden** unless the user's `loyaltyTier >= 3`.
- This applies regardless of the user's permission tier (viewer, member, or admin).
  Even admins must meet the loyalty tier requirement to create reservations on
  premium properties.
- All other actions (viewProperty, updateProperty, viewReservation, etc.) are
  unaffected by the loyalty tier or premium flag.

## Notes (Loyalty Tiers)
- The forbid rule checks: `resource.isPremium == true` AND `principal.loyaltyTier < 3`.
- This is a cross-entity numeric comparison: a Long attribute on the principal
  is compared against a threshold.
