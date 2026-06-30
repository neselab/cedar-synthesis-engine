permit (
  principal,
  action == Action::"access",
  resource
)
when {
  principal is User &&
  resource is System &&
  principal.role == "user" &&
  context.inBlackoutWindow == false
};

permit (
  principal,
  action == Action::"access",
  resource
)
when {
  principal is User &&
  resource is System &&
  principal.role == "oncall"
};

permit (
  principal,
  action == Action::"emergencyAccess",
  resource
)
when {
  principal is User &&
  resource is System &&
  principal.role == "oncall" &&
  context.inBlackoutWindow == true
};

forbid (
  principal,
  action == Action::"emergencyAccess",
  resource
)
when {
  principal is User &&
  resource is System &&
  context.inBlackoutWindow == false
};