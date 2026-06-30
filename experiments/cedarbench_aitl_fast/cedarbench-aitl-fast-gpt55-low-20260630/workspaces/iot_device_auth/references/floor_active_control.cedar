permit (principal is Device, action == Action::"control", resource is Endpoint)
when { principal.isActive && principal.capabilities.contains("actuate") };
