"""Hotel chain permissions mutations."""

from cedarbench.mutation import Mutation, MutationMeta, MutationResult, register
from cedarbench import schema_ops

# -- Base policy spec (shared starting point) ---------------------------------

_BASE_SPEC = """\
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
"""


# -- Helpers -------------------------------------------------------------------

def _hotel_base_schema() -> str:
    """The base hotel chain schema."""
    return """\
// Hotel Chain Permissions -- Cedar Schema

type PermissionsMap = {
  hotelReservations: Set<Hotel>,
  propertyReservations: Set<Property>,
};
entity User {
  viewPermissions: PermissionsMap,
  memberPermissions: PermissionsMap,
  hotelAdminPermissions: Set<Hotel>,
  propertyAdminPermissions: Set<Property>,
};
entity Property in [Hotel];
entity Hotel in [Hotel];
entity Reservation in [Property];

// ACTIONS: Reservations
action viewReservation, updateReservation, grantAccessReservation
  appliesTo {
    principal: User,
    resource: Reservation,
  };

// ACTIONS: Properties (plus, CreateReservation for a Property)
action createReservation, viewProperty, updateProperty, grantAccessProperty
  appliesTo {
    principal: User,
    resource: Property,
  };

// ACTIONS: Hotels (plus, CreateProperty for a Hotel)
action createProperty, createHotel, viewHotel, updateHotel, grantAccessHotel
  appliesTo {
    principal: User,
    resource: Hotel,
  };
"""


# -- Easy Mutations ------------------------------------------------------------

class HotelAddGuest(Mutation):
    def meta(self):
        return MutationMeta(
            id="hotel_add_guest",
            base_scenario="hotel",
            difficulty="easy",
            description="Add Guest role: view-only reservations where guest is the reservation subject",
            operators=["S6", "S9", "P2"],
            features_tested=["new_entity", "self_access", "view_only"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = """\
// Hotel Chain Permissions -- Cedar Schema

type PermissionsMap = {
  hotelReservations: Set<Hotel>,
  propertyReservations: Set<Property>,
};
entity User {
  viewPermissions: PermissionsMap,
  memberPermissions: PermissionsMap,
  hotelAdminPermissions: Set<Hotel>,
  propertyAdminPermissions: Set<Property>,
};
entity Guest {
  reservations: Set<Reservation>,
};
entity Property in [Hotel];
entity Hotel in [Hotel];
entity Reservation in [Property] {
  guest: Guest,
};

// ACTIONS: Reservations
action viewReservation, updateReservation, grantAccessReservation
  appliesTo {
    principal: User,
    resource: Reservation,
  };

// Guest actions on Reservations
action guestViewReservation appliesTo {
    principal: Guest,
    resource: Reservation,
  };

// ACTIONS: Properties (plus, CreateReservation for a Property)
action createReservation, viewProperty, updateProperty, grantAccessProperty
  appliesTo {
    principal: User,
    resource: Property,
  };

// ACTIONS: Hotels (plus, CreateProperty for a Hotel)
action createProperty, createHotel, viewHotel, updateHotel, grantAccessHotel
  appliesTo {
    principal: User,
    resource: Hotel,
  };
"""
        spec = _BASE_SPEC + """\
### 7. Guest Permissions
- A new **Guest** entity type exists with a `reservations: Set<Reservation>` attribute.
- Reservations now have a `guest: Guest` attribute linking them to the guest who booked.
- A Guest may **guestViewReservation** on a Reservation ONLY if `resource in principal.reservations`
  (i.e., the reservation is in the guest's reservation set).
- Guests have no other permissions -- they cannot update, create, or grant access to anything.
- Guests are completely separate from Users and have no viewer/member/admin permissions.
"""
        return MutationResult(schema=schema, policy_spec=spec)


class HotelAddCancel(Mutation):
    def meta(self):
        return MutationMeta(
            id="hotel_add_cancel",
            base_scenario="hotel",
            difficulty="easy",
            description="Add cancelReservation action; member or admin only",
            operators=["S7", "P2"],
            features_tested=["new_action", "tiered_access"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = base_schema.replace(
            "action viewReservation, updateReservation, grantAccessReservation",
            "action viewReservation, updateReservation, grantAccessReservation, cancelReservation"
        )
        spec = _BASE_SPEC + """\
### 7. Cancel Reservation
- A new **cancelReservation** action is available on Reservations.
- A user may **cancelReservation** if the reservation is in the user's
  `memberPermissions.hotelReservations` or `memberPermissions.propertyReservations`
  (same tier as updateReservation).
- A user may also **cancelReservation** if the reservation is in the user's
  `hotelAdminPermissions` or `propertyAdminPermissions`.
- Viewers (viewPermissions only) may NOT cancel reservations.
"""
        return MutationResult(schema=schema, policy_spec=spec)


class HotelRemoveHierarchy(Mutation):
    def meta(self):
        return MutationMeta(
            id="hotel_remove_hierarchy",
            base_scenario="hotel",
            difficulty="easy",
            description="Remove Property in Hotel inheritance; flatten hierarchy",
            operators=["S10", "P3", "P8"],
            features_tested=["hierarchy_removal", "flattening"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = """\
// Hotel Chain Permissions -- Cedar Schema (Flat)

type PermissionsMap = {
  hotelReservations: Set<Hotel>,
  propertyReservations: Set<Property>,
};
entity User {
  viewPermissions: PermissionsMap,
  memberPermissions: PermissionsMap,
  hotelAdminPermissions: Set<Hotel>,
  propertyAdminPermissions: Set<Property>,
};
entity Property;
entity Hotel in [Hotel];
entity Reservation in [Property];

// ACTIONS: Reservations
action viewReservation, updateReservation, grantAccessReservation
  appliesTo {
    principal: User,
    resource: Reservation,
  };

// ACTIONS: Properties (plus, CreateReservation for a Property)
action createReservation, viewProperty, updateProperty, grantAccessProperty
  appliesTo {
    principal: User,
    resource: Property,
  };

// ACTIONS: Hotels (plus, CreateProperty for a Hotel)
action createProperty, createHotel, viewHotel, updateHotel, grantAccessHotel
  appliesTo {
    principal: User,
    resource: Hotel,
  };
"""
        spec = """\
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
"""
        return MutationResult(schema=schema, policy_spec=spec)


# -- Medium Mutations ----------------------------------------------------------

class HotelAddRenovationLock(Mutation):
    def meta(self):
        return MutationMeta(
            id="hotel_add_renovation_lock",
            base_scenario="hotel",
            difficulty="medium",
            description="Add isUnderRenovation Bool on Property; forbid createReservation unless admin",
            operators=["S1", "P1", "P4"],
            features_tested=["boolean_guard", "forbid_with_exception", "admin_bypass"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = """\
// Hotel Chain Permissions -- Cedar Schema

type PermissionsMap = {
  hotelReservations: Set<Hotel>,
  propertyReservations: Set<Property>,
};
entity User {
  viewPermissions: PermissionsMap,
  memberPermissions: PermissionsMap,
  hotelAdminPermissions: Set<Hotel>,
  propertyAdminPermissions: Set<Property>,
};
entity Property in [Hotel] {
  isUnderRenovation: Bool,
};
entity Hotel in [Hotel];
entity Reservation in [Property];

// ACTIONS: Reservations
action viewReservation, updateReservation, grantAccessReservation
  appliesTo {
    principal: User,
    resource: Reservation,
  };

// ACTIONS: Properties (plus, CreateReservation for a Property)
action createReservation, viewProperty, updateProperty, grantAccessProperty
  appliesTo {
    principal: User,
    resource: Property,
  };

// ACTIONS: Hotels (plus, CreateProperty for a Hotel)
action createProperty, createHotel, viewHotel, updateHotel, grantAccessHotel
  appliesTo {
    principal: User,
    resource: Hotel,
  };
"""
        spec = _BASE_SPEC + """\
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
"""
        return MutationResult(schema=schema, policy_spec=spec)


class HotelAddFranchise(Mutation):
    def meta(self):
        return MutationMeta(
            id="hotel_add_franchise",
            base_scenario="hotel",
            difficulty="medium",
            description="Add Franchise entity above Hotel; 4-level hierarchy with franchise-level actions",
            operators=["S6", "S7", "S8", "P2"],
            features_tested=["new_entity", "deeper_hierarchy", "new_actions"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = """\
// Hotel Chain Permissions -- Cedar Schema (with Franchise)

type PermissionsMap = {
  franchiseReservations: Set<Franchise>,
  hotelReservations: Set<Hotel>,
  propertyReservations: Set<Property>,
};
entity User {
  viewPermissions: PermissionsMap,
  memberPermissions: PermissionsMap,
  franchiseAdminPermissions: Set<Franchise>,
  hotelAdminPermissions: Set<Hotel>,
  propertyAdminPermissions: Set<Property>,
};
entity Franchise;
entity Property in [Hotel];
entity Hotel in [Hotel, Franchise];
entity Reservation in [Property];

// ACTIONS: Reservations
action viewReservation, updateReservation, grantAccessReservation
  appliesTo {
    principal: User,
    resource: Reservation,
  };

// ACTIONS: Properties (plus, CreateReservation for a Property)
action createReservation, viewProperty, updateProperty, grantAccessProperty
  appliesTo {
    principal: User,
    resource: Property,
  };

// ACTIONS: Hotels (plus, CreateProperty for a Hotel)
action createProperty, createHotel, viewHotel, updateHotel, grantAccessHotel
  appliesTo {
    principal: User,
    resource: Hotel,
  };

// ACTIONS: Franchises
action viewFranchise, updateFranchise, grantAccessFranchise
  appliesTo {
    principal: User,
    resource: Franchise,
  };
"""
        spec = """\
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
"""
        return MutationResult(schema=schema, policy_spec=spec)


class HotelAddLoyaltyTier(Mutation):
    def meta(self):
        return MutationMeta(
            id="hotel_add_loyalty_tier",
            base_scenario="hotel",
            difficulty="medium",
            description="Add loyaltyTier Long on User; premium properties require tier >= 3",
            operators=["S2", "S1", "P1", "P10"],
            features_tested=["numeric_comparison", "boolean_guard", "cross_entity_constraint"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = """\
// Hotel Chain Permissions -- Cedar Schema (with Loyalty Tiers)

type PermissionsMap = {
  hotelReservations: Set<Hotel>,
  propertyReservations: Set<Property>,
};
entity User {
  viewPermissions: PermissionsMap,
  memberPermissions: PermissionsMap,
  hotelAdminPermissions: Set<Hotel>,
  propertyAdminPermissions: Set<Property>,
  loyaltyTier: Long,
};
entity Property in [Hotel] {
  isPremium: Bool,
};
entity Hotel in [Hotel];
entity Reservation in [Property];

// ACTIONS: Reservations
action viewReservation, updateReservation, grantAccessReservation
  appliesTo {
    principal: User,
    resource: Reservation,
  };

// ACTIONS: Properties (plus, CreateReservation for a Property)
action createReservation, viewProperty, updateProperty, grantAccessProperty
  appliesTo {
    principal: User,
    resource: Property,
  };

// ACTIONS: Hotels (plus, CreateProperty for a Hotel)
action createProperty, createHotel, viewHotel, updateHotel, grantAccessHotel
  appliesTo {
    principal: User,
    resource: Hotel,
  };
"""
        spec = _BASE_SPEC + """\
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
"""
        return MutationResult(schema=schema, policy_spec=spec)


# -- Hard Mutations ------------------------------------------------------------

class HotelFranchiseLoyalty(Mutation):
    def meta(self):
        return MutationMeta(
            id="hotel_franchise_loyalty",
            base_scenario="hotel",
            difficulty="hard",
            description="Franchise hierarchy + loyalty tiers + renovation lock combined",
            operators=["S6", "S7", "S8", "S2", "S1", "S1", "P1", "P2", "P4", "P10"],
            features_tested=["multi_mutation", "complex_hierarchy", "numeric_guard", "forbid_interaction"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = """\
// Hotel Chain Permissions -- Cedar Schema (Franchise + Loyalty + Renovation)

type PermissionsMap = {
  franchiseReservations: Set<Franchise>,
  hotelReservations: Set<Hotel>,
  propertyReservations: Set<Property>,
};
entity User {
  viewPermissions: PermissionsMap,
  memberPermissions: PermissionsMap,
  franchiseAdminPermissions: Set<Franchise>,
  hotelAdminPermissions: Set<Hotel>,
  propertyAdminPermissions: Set<Property>,
  loyaltyTier: Long,
};
entity Franchise;
entity Property in [Hotel] {
  isUnderRenovation: Bool,
  isPremium: Bool,
};
entity Hotel in [Hotel, Franchise];
entity Reservation in [Property];

// ACTIONS: Reservations
action viewReservation, updateReservation, grantAccessReservation
  appliesTo {
    principal: User,
    resource: Reservation,
  };

// ACTIONS: Properties (plus, CreateReservation for a Property)
action createReservation, viewProperty, updateProperty, grantAccessProperty
  appliesTo {
    principal: User,
    resource: Property,
  };

// ACTIONS: Hotels (plus, CreateProperty for a Hotel)
action createProperty, createHotel, viewHotel, updateHotel, grantAccessHotel
  appliesTo {
    principal: User,
    resource: Hotel,
  };

// ACTIONS: Franchises
action viewFranchise, updateFranchise, grantAccessFranchise
  appliesTo {
    principal: User,
    resource: Franchise,
  };
"""
        spec = """\
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
"""
        return MutationResult(schema=schema, policy_spec=spec)


class HotelTemporalRates(Mutation):
    def meta(self):
        return MutationMeta(
            id="hotel_temporal_rates",
            base_scenario="hotel",
            difficulty="hard",
            description="Add seasonStart/seasonEnd datetime on Property; rate viewing restricted to season window",
            operators=["S4", "S4", "S7", "P1", "P2", "P10"],
            features_tested=["datetime_comparison", "temporal_window", "new_action", "context_time"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = """\
// Hotel Chain Permissions -- Cedar Schema (with Temporal Rates)

type PermissionsMap = {
  hotelReservations: Set<Hotel>,
  propertyReservations: Set<Property>,
};
entity User {
  viewPermissions: PermissionsMap,
  memberPermissions: PermissionsMap,
  hotelAdminPermissions: Set<Hotel>,
  propertyAdminPermissions: Set<Property>,
};
entity Property in [Hotel] {
  seasonStart: Long,
  seasonEnd: Long,
};
entity Hotel in [Hotel];
entity Reservation in [Property];

// ACTIONS: Reservations
action viewReservation, updateReservation, grantAccessReservation
  appliesTo {
    principal: User,
    resource: Reservation,
  };

// ACTIONS: Properties (plus, CreateReservation for a Property)
action createReservation, viewProperty, updateProperty, grantAccessProperty
  appliesTo {
    principal: User,
    resource: Property,
  };

// ACTIONS: Hotels (plus, CreateProperty for a Hotel)
action createProperty, createHotel, viewHotel, updateHotel, grantAccessHotel
  appliesTo {
    principal: User,
    resource: Hotel,
  };

// ACTION: View seasonal rates (requires time context)
action viewRates appliesTo {
    principal: User,
    resource: Property,
    context: { currentTime: Long },
  };
"""
        spec = _BASE_SPEC + """\
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
"""
        return MutationResult(schema=schema, policy_spec=spec)


# -- Registration --------------------------------------------------------------

MUTATIONS = [
    HotelAddGuest(),
    HotelAddCancel(),
    HotelRemoveHierarchy(),
    HotelAddRenovationLock(),
    HotelAddFranchise(),
    HotelAddLoyaltyTier(),
    HotelFranchiseLoyalty(),
    HotelTemporalRates(),
]

for m in MUTATIONS:
    register(m)
