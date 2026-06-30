// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
permit (
  principal is Customer,
  action == Action::"viewContact",
  resource is Customer
)
when {
  principal == resource
};

permit (
  principal is Vendor,
  action == Action::"viewContact",
  resource is Vendor
)
when {
  principal == resource
};

permit (
  principal is Employee,
  action == Action::"viewContact",
  resource is Employee
)
when {
  principal == resource
};

permit (
  principal is Admin,
  action == Action::"viewContact",
  resource is Customer
);

permit (
  principal is Admin,
  action == Action::"viewContact",
  resource is Vendor
);

permit (
  principal is Admin,
  action == Action::"viewContact",
  resource is Employee
);

permit (
  principal is Customer,
  action == Action::"updateContact",
  resource is Customer
)
when {
  principal == resource
};

permit (
  principal is Vendor,
  action == Action::"updateContact",
  resource is Vendor
)
when {
  principal == resource
};

permit (
  principal is Employee,
  action == Action::"updateContact",
  resource is Employee
)
when {
  principal == resource
};

permit (
  principal is Admin,
  action == Action::"verifyAddress",
  resource is Customer
)
when {
  resource.contact.address.country == "US"
};

permit (
  principal is Admin,
  action == Action::"verifyAddress",
  resource is Vendor
)
when {
  resource.contact.address.country == "US"
};

permit (
  principal is Admin,
  action == Action::"verifyAddress",
  resource is Employee
)
when {
  resource.contact.address.country == "US"
};
