permit (principal is Device, action == Action::"telemetry", resource is Endpoint)
when { principal.isActive && principal.capabilities.contains("read_sensor") };
