permit (
  principal is User,
  action == Action::"viewReservation",
  resource is Reservation
) when {
  resource in principal.viewPermissions.hotelReservations ||
  resource in principal.viewPermissions.propertyReservations
};

permit (
  principal is User,
  action in [
    Action::"viewReservation",
    Action::"updateReservation",
    Action::"cancelReservation"
  ],
  resource is Reservation
) when {
  resource in principal.memberPermissions.hotelReservations ||
  resource in principal.memberPermissions.propertyReservations
};

permit (
  principal is User,
  action == Action::"createReservation",
  resource is Property
) when {
  resource in principal.memberPermissions.hotelReservations ||
  resource in principal.memberPermissions.propertyReservations
};

permit (
  principal is User,
  action in [
    Action::"viewReservation",
    Action::"updateReservation",
    Action::"grantAccessReservation",
    Action::"cancelReservation"
  ],
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
  resource in principal.hotelAdminPermissions ||
  resource in principal.propertyAdminPermissions
};

permit (
  principal is User,
  action == Action::"viewProperty",
  resource is Property
) when {
  resource in principal.viewPermissions.hotelReservations ||
  resource in principal.viewPermissions.propertyReservations
};

permit (
  principal is User,
  action == Action::"viewHotel",
  resource is Hotel
) when {
  resource in principal.viewPermissions.hotelReservations
};

permit (
  principal is User,
  action in [
    Action::"viewProperty",
    Action::"updateProperty"
  ],
  resource is Property
) when {
  resource in principal.memberPermissions.hotelReservations ||
  resource in principal.memberPermissions.propertyReservations
};

permit (
  principal is User,
  action in [
    Action::"createProperty",
    Action::"viewHotel",
    Action::"updateHotel",
    Action::"createHotel"
  ],
  resource is Hotel
) when {
  resource in principal.memberPermissions.hotelReservations
};

permit (
  principal is User,
  action in [
    Action::"viewProperty",
    Action::"updateProperty",
    Action::"grantAccessProperty"
  ],
  resource is Property
) when {
  resource in principal.hotelAdminPermissions ||
  resource in principal.propertyAdminPermissions
};

permit (
  principal is User,
  action in [
    Action::"createProperty",
    Action::"viewHotel",
    Action::"updateHotel",
    Action::"grantAccessHotel",
    Action::"createHotel"
  ],
  resource is Hotel
) when {
  resource in principal.hotelAdminPermissions
};