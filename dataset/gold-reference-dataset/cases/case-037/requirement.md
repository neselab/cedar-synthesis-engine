Device Telemetry Access

A user may read telemetry only if they hold the operator or fleet administrator role, own the device associated with the telemetry, and that device has decommissioned status. The user's clearance and the telemetry's sensitivity must each be 0, 1, or 2, and the user's clearance must be at least the telemetry's sensitivity. The request's source IP address must be within 192.168.0.0/16.

These are the only permissions: reading device telemetry is allowed when all these requirements are met, and all other requests are denied.
