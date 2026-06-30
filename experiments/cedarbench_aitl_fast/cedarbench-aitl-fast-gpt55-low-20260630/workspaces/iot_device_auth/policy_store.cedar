// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
permit (
  principal is Device,
  action == Action::"telemetry",
  resource is Endpoint
)
when {
  principal.isActive == true &&
  principal.capabilities.contains("read_sensor")
};

permit (
  principal is Device,
  action == Action::"control",
  resource is Endpoint
)
when {
  principal.isActive == true &&
  principal.capabilities.contains("actuate")
};

permit (
  principal is Device,
  action == Action::"stream",
  resource is Endpoint
)
when {
  principal.isActive == true &&
  principal.capabilities.contains("stream")
};

permit (
  principal is User,
  action == Action::"manage",
  resource is Endpoint
)
when {
  principal == resource.owner
};
