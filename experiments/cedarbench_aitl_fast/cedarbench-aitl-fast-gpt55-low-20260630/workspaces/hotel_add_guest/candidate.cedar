permit (
  principal,
  action == Action::"viewReservation",
  resource
)
when {
  principal is User &&
  resource is Reservation &&
  (
    resource in principal.viewPermissions.hotelReservations ||
    resource in principal.viewPermissions.propertyReservations ||
    resource in principal.memberPermissions.hotelReservations ||
    resource in principal.memberPermissions.propertyReservations ||
    resource in principal.hotelAdminPermissions ||
    resource in principal.propertyAdminPermissions
  )
};

permit (
  principal,
  action == Action::"updateReservation",
  resource
)
when {
  principal is User &&
  resource is Reservation &&
  (
    resource in principal.memberPermissions.hotelReservations ||
    resource in principal.memberPermissions.propertyReservations ||
    resource in principal.hotelAdminPermissions ||
    resource in principal.propertyAdminPermissions
  )
};

permit (
  principal,
  action == Action::"grantAccessReservation",
  resource
)
when {
  principal is User &&
  resource is Reservation &&
  (
    resource in principal.hotelAdminPermissions ||
    resource in principal.propertyAdminPermissions
  )
};

permit (
  principal,
  action == Action::"createReservation",
  resource
)
when {
  principal is User &&
  resource is Property &&
  (
    resource in principal.memberPermissions.hotelReservations ||
    resource in principal.memberPermissions.propertyReservations ||
    resource in principal.hotelAdminPermissions ||
    resource in principal.propertyAdminPermissions
  )
};

permit (
  principal,
  action == Action::"guestViewReservation",
  resource
)
when {
  principal is Guest &&
  resource is Reservation &&
  resource in principal.reservations
};

permit (
  principal,
  action == Action::"viewProperty",
  resource
)
when {
  principal is User &&
  resource is Property &&
  (
    resource in principal.viewPermissions.hotelReservations ||
    resource in principal.viewPermissions.propertyReservations ||
    resource in principal.memberPermissions.hotelReservations ||
    resource in principal.memberPermissions.propertyReservations ||
    resource in principal.hotelAdminPermissions ||
    resource in principal.propertyAdminPermissions
  )
};

permit (
  principal,
  action == Action::"updateProperty",
  resource
)
when {
  principal is User &&
  resource is Property &&
  (
    resource in principal.memberPermissions.hotelReservations ||
    resource in principal.memberPermissions.propertyReservations ||
    resource in principal.hotelAdminPermissions ||
    resource in principal.propertyAdminPermissions
  )
};

permit (
  principal,
  action == Action::"grantAccessProperty",
  resource
)
when {
  principal is User &&
  resource is Property &&
  (
    resource in principal.hotelAdminPermissions ||
    resource in principal.propertyAdminPermissions
  )
};

permit (
  principal,
  action == Action::"viewHotel",
  resource
)
when {
  principal is User &&
  resource is Hotel &&
  (
    resource in principal.viewPermissions.hotelReservations ||
    resource in principal.memberPermissions.hotelReservations ||
    resource in principal.hotelAdminPermissions
  )
};

permit (
  principal,
  action == Action::"updateHotel",
  resource
)
when {
  principal is User &&
  resource is Hotel &&
  (
    resource in principal.memberPermissions.hotelReservations ||
    resource in principal.hotelAdminPermissions
  )
};

permit (
  principal,
  action == Action::"createHotel",
  resource
)
when {
  principal is User &&
  resource is Hotel &&
  (
    resource in principal.memberPermissions.hotelReservations ||
    resource in principal.hotelAdminPermissions
  )
};

permit (
  principal,
  action == Action::"createProperty",
  resource
)
when {
  principal is User &&
  resource is Hotel &&
  (
    resource in principal.memberPermissions.hotelReservations ||
    resource in principal.hotelAdminPermissions
  )
};

permit (
  principal,
  action == Action::"grantAccessHotel",
  resource
)
when {
  principal is User &&
  resource is Hotel &&
  resource in principal.hotelAdminPermissions
};