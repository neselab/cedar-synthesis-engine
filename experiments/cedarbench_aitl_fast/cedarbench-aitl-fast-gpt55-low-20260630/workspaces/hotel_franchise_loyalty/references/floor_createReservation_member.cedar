permit (
    principal is User,
    action == Action::"createReservation",
    resource is Property
)
when {
    resource in principal.memberPermissions.propertyReservations &&
    resource.isUnderRenovation == false &&
    (resource.isPremium == false || principal.loyaltyTier >= 3)
};