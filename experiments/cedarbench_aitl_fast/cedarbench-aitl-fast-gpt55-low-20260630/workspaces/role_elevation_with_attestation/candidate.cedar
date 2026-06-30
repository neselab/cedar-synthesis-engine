permit (
  principal is User,
  action == Action::"accessNormal",
  resource is SensitiveResource
)
when {
  principal.baseRole == "user" ||
  principal.baseRole == "lead" ||
  principal.baseRole == "manager"
};

permit (
  principal is User,
  action == Action::"accessSensitive",
  resource is SensitiveResource
)
when {
  principal.baseRole == "manager"
};

permit (
  principal is User,
  action == Action::"accessSensitive",
  resource is SensitiveResource
)
when {
  (principal.baseRole == "user" || principal.baseRole == "lead") &&
  principal.elevationGranted == true &&
  (context has elevationJustification) &&
  context.elevationJustification != ""
};