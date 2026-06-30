forbid (
  principal is User,
  action == Action::"createReservation",
  resource is Property
)
when {
  resource.isUnderRenovation == true
}
unless {
  resource in principal.franchiseAdminPermissions ||
  resource in principal.hotelAdminPermissions ||
  resource in principal.propertyAdminPermissions
};

forbid (
  principal is User,
  action == Action::"createReservation",
  resource is Property
)
when {
  resource.isPremium == true &&
  principal.loyaltyTier < 3
};

permit (
  principal is User,
  action == Action::"viewReservation",
  resource is Reservation
)
when {
  resource in principal.viewPermissions.franchiseReservations ||
  resource in principal.viewPermissions.hotelReservations ||
  resource in principal.viewPermissions.propertyReservations ||
  resource in principal.memberPermissions.franchiseReservations ||
  resource in principal.memberPermissions.hotelReservations ||
  resource in principal.memberPermissions.propertyReservations ||
  resource in principal.franchiseAdminPermissions ||
  resource in principal.hotelAdminPermissions ||
  resource in principal.propertyAdminPermissions
};

permit (
  principal is User,
  action == Action::"updateReservation",
  resource is Reservation
)
when {
  resource in principal.memberPermissions.franchiseReservations ||
  resource in principal.memberPermissions.hotelReservations ||
  resource in principal.memberPermissions.propertyReservations ||
  resource in principal.franchiseAdminPermissions ||
  resource in principal.hotelAdminPermissions ||
  resource in principal.propertyAdminPermissions
};

permit (
  principal is User,
  action == Action::"grantAccessReservation",
  resource is Reservation
)
when {
  resource in principal.franchiseAdminPermissions ||
  resource in principal.hotelAdminPermissions ||
  resource in principal.propertyAdminPermissions
};

permit (
  principal is User,
  action == Action::"createReservation",
  resource is Property
)
when {
  resource in principal.memberPermissions.franchiseReservations ||
  resource in principal.memberPermissions.hotelReservations ||
  resource in principal.memberPermissions.propertyReservations ||
  resource in principal.franchiseAdminPermissions ||
  resource in principal.hotelAdminPermissions ||
  resource in principal.propertyAdminPermissions
};

permit (
  principal is User,
  action == Action::"viewProperty",
  resource is Property
)
when {
  resource in principal.viewPermissions.franchiseReservations ||
  resource in principal.viewPermissions.hotelReservations ||
  resource in principal.viewPermissions.propertyReservations ||
  resource in principal.memberPermissions.franchiseReservations ||
  resource in principal.memberPermissions.hotelReservations ||
  resource in principal.memberPermissions.propertyReservations ||
  resource in principal.franchiseAdminPermissions ||
  resource in principal.hotelAdminPermissions ||
  resource in principal.propertyAdminPermissions
};

permit (
  principal is User,
  action == Action::"updateProperty",
  resource is Property
)
when {
  resource in principal.memberPermissions.franchiseReservations ||
  resource in principal.memberPermissions.hotelReservations ||
  resource in principal.memberPermissions.propertyReservations ||
  resource in principal.franchiseAdminPermissions ||
  resource in principal.hotelAdminPermissions ||
  resource in principal.propertyAdminPermissions
};

permit (
  principal is User,
  action == Action::"grantAccessProperty",
  resource is Property
)
when {
  resource in principal.franchiseAdminPermissions ||
  resource in principal.hotelAdminPermissions ||
  resource in principal.propertyAdminPermissions
};

permit (
  principal is User,
  action == Action::"viewHotel",
  resource is Hotel
)
when {
  resource in principal.viewPermissions.franchiseReservations ||
  resource in principal.viewPermissions.hotelReservations ||
  resource in principal.memberPermissions.franchiseReservations ||
  resource in principal.memberPermissions.hotelReservations ||
  resource in principal.franchiseAdminPermissions ||
  resource in principal.hotelAdminPermissions
};

permit (
  principal is User,
  action == Action::"updateHotel",
  resource is Hotel
)
when {
  resource in principal.memberPermissions.franchiseReservations ||
  resource in principal.memberPermissions.hotelReservations ||
  resource in principal.franchiseAdminPermissions ||
  resource in principal.hotelAdminPermissions
};

permit (
  principal is User,
  action == Action::"grantAccessHotel",
  resource is Hotel
)
when {
  resource in principal.franchiseAdminPermissions ||
  resource in principal.hotelAdminPermissions
};

permit (
  principal is User,
  action == Action::"createProperty",
  resource is Hotel
)
when {
  resource in principal.memberPermissions.franchiseReservations ||
  resource in principal.memberPermissions.hotelReservations ||
  resource in principal.franchiseAdminPermissions ||
  resource in principal.hotelAdminPermissions
};

permit (
  principal is User,
  action == Action::"createHotel",
  resource is Hotel
)
when {
  resource in principal.memberPermissions.franchiseReservations ||
  resource in principal.memberPermissions.hotelReservations ||
  resource in principal.franchiseAdminPermissions ||
  resource in principal.hotelAdminPermissions
};

permit (
  principal is User,
  action == Action::"viewFranchise",
  resource is Franchise
)
when {
  resource in principal.viewPermissions.franchiseReservations ||
  resource in principal.memberPermissions.franchiseReservations ||
  resource in principal.franchiseAdminPermissions
};

permit (
  principal is User,
  action == Action::"updateFranchise",
  resource is Franchise
)
when {
  resource in principal.memberPermissions.franchiseReservations ||
  resource in principal.franchiseAdminPermissions
};

permit (
  principal is User,
  action == Action::"grantAccessFranchise",
  resource is Franchise
)
when {
  resource in principal.franchiseAdminPermissions
};