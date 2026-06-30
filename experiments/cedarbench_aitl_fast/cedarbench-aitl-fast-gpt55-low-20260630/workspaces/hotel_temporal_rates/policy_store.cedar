// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
permit (
  principal is User,
  action == Action::"viewReservation",
  resource is Reservation
) when {
  resource in principal.viewPermissions.hotelReservations ||
  resource in principal.viewPermissions.propertyReservations ||
  resource in principal.memberPermissions.hotelReservations ||
  resource in principal.memberPermissions.propertyReservations ||
  resource in principal.hotelAdminPermissions ||
  resource in principal.propertyAdminPermissions
};

permit (
  principal is User,
  action == Action::"updateReservation",
  resource is Reservation
) when {
  resource in principal.memberPermissions.hotelReservations ||
  resource in principal.memberPermissions.propertyReservations ||
  resource in principal.hotelAdminPermissions ||
  resource in principal.propertyAdminPermissions
};

permit (
  principal is User,
  action == Action::"grantAccessReservation",
  resource is Reservation
) when {
  resource in principal.hotelAdminPermissions ||
  resource in principal.propertyAdminPermissions
};

permit (
  principal is User,
  action == Action::"createReservation",
  resource is Property
) when {
  resource in principal.memberPermissions.hotelReservations ||
  resource in principal.memberPermissions.propertyReservations ||
  resource in principal.hotelAdminPermissions ||
  resource in principal.propertyAdminPermissions
};

permit (
  principal is User,
  action == Action::"viewProperty",
  resource is Property
) when {
  resource in principal.viewPermissions.hotelReservations ||
  resource in principal.viewPermissions.propertyReservations ||
  resource in principal.memberPermissions.hotelReservations ||
  resource in principal.memberPermissions.propertyReservations ||
  resource in principal.hotelAdminPermissions ||
  resource in principal.propertyAdminPermissions
};

permit (
  principal is User,
  action == Action::"updateProperty",
  resource is Property
) when {
  resource in principal.memberPermissions.hotelReservations ||
  resource in principal.memberPermissions.propertyReservations ||
  resource in principal.hotelAdminPermissions ||
  resource in principal.propertyAdminPermissions
};

permit (
  principal is User,
  action == Action::"grantAccessProperty",
  resource is Property
) when {
  resource in principal.hotelAdminPermissions ||
  resource in principal.propertyAdminPermissions
};

permit (
  principal is User,
  action == Action::"viewHotel",
  resource is Hotel
) when {
  resource in principal.viewPermissions.hotelReservations ||
  resource in principal.memberPermissions.hotelReservations ||
  resource in principal.hotelAdminPermissions
};

permit (
  principal is User,
  action == Action::"updateHotel",
  resource is Hotel
) when {
  resource in principal.memberPermissions.hotelReservations ||
  resource in principal.hotelAdminPermissions
};

permit (
  principal is User,
  action == Action::"createProperty",
  resource is Hotel
) when {
  resource in principal.memberPermissions.hotelReservations ||
  resource in principal.hotelAdminPermissions
};

permit (
  principal is User,
  action == Action::"createHotel",
  resource is Hotel
) when {
  resource in principal.memberPermissions.hotelReservations ||
  resource in principal.hotelAdminPermissions
};

permit (
  principal is User,
  action == Action::"grantAccessHotel",
  resource is Hotel
) when {
  resource in principal.hotelAdminPermissions
};

forbid (
  principal is User,
  action == Action::"viewRates",
  resource is Property
) when {
  context.currentTime < resource.seasonStart ||
  context.currentTime > resource.seasonEnd
} unless {
  resource in principal.hotelAdminPermissions ||
  resource in principal.propertyAdminPermissions
};

permit (
  principal is User,
  action == Action::"viewRates",
  resource is Property
) when {
  (
    resource in principal.viewPermissions.hotelReservations ||
    resource in principal.viewPermissions.propertyReservations ||
    resource in principal.memberPermissions.hotelReservations ||
    resource in principal.memberPermissions.propertyReservations
  ) &&
  context.currentTime >= resource.seasonStart &&
  context.currentTime <= resource.seasonEnd
};

permit (
  principal is User,
  action == Action::"viewRates",
  resource is Property
) when {
  resource in principal.hotelAdminPermissions ||
  resource in principal.propertyAdminPermissions
};
