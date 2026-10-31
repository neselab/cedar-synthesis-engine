Device Command Access

A user may send a command to a device only if the user holds at least one of the operator, technician, or fleet administrator roles. The device must have the security_patch firmware tag, the user’s membership group must be the same as or descend from the device’s site group, and the request’s source IP address must be within 172.16.0.0/12.

The device must be active unless the request’s maintenance window flag is true, the user holds the technician role, and the device is in maintenance status. This exception waives only the active-status requirement; all other requirements still apply.

These are the only permissions: a device command is permitted if and only if all applicable requirements above are met, and no other actions are permitted.
