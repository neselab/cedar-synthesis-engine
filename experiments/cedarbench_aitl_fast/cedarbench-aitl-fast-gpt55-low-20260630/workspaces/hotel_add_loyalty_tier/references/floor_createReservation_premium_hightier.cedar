permit (
    principal is User,
    action == Action::"createReservation",
    resource is Property
) when {
    resource in principal.memberPermissions.hotelReservations &&
    resource.isPremium == true &&
    principal.loyaltyTier >= 3
};