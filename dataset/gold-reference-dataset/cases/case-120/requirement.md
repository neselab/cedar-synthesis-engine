Device Command Access

A user may send a command to a device only if the user holds at least one of the operator, technician, or fleet administrator roles, the device is active, and the user owns the device. The user's membership group must be the same as, or descend from, the device's site group, and the request's source IP address must be within 192.168.0.0/16.

These are the only permissions: a request is allowed if and only if all these requirements are met, and no other action is permitted under this requirement.
