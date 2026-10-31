Device Command Access

A user may send a command to a device only if the user holds at least one of the operator, technician, or fleet administrator roles, the device is active, and its firmware tags include “beta”. The user’s membership group must be the same as, or a descendant of, the device’s site group, and the request’s source IP address must be within 192.168.0.0/16.

These are the only permissions: sending a device command is permitted when all of these requirements are met, and no other actions are authorized.
