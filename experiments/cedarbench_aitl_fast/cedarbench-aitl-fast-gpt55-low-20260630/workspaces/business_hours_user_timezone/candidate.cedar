permit (
  principal,
  action == Action::"access",
  resource
)
when {
  principal is Employee &&
  resource is System &&
  context.now.offset(principal.timezoneOffset).toTime() >= duration("9h") &&
  context.now.offset(principal.timezoneOffset).toTime() < duration("17h")
};

permit (
  principal,
  action == Action::"report",
  resource
)
when {
  principal is Employee &&
  resource is System
};