permit (principal is Device, action == Action::"stream", resource is Endpoint)
when { principal.isActive && principal.capabilities.contains("stream") };
