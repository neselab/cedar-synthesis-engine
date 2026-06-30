permit (
    principal is User,
    action == Action::"createReservation",
    resource is Property
)
when {
    resource in principal.propertyAdminPermissions &&
    resource.isUnderRenovation == true &&
    (resource.isPremium == false || principal.loyaltyTier >= 3)
};