Sending Device Commands

A user may send a command to a device only if the user holds at least one of the operator, technician, or fleet administrator roles, the device is active, and its firmware tags include “stable”. The request’s current time must be at or after its scheduled start time and strictly before its scheduled end time. Times are in UTC. The request’s source IP address must be within 10.0.0.0/8.

If the device is in maintenance mode, the maintenance command must also be authorized. This additional requirement applies only while maintenance mode is enabled; all other requirements still apply.

These are the only permissions: sending a device command is allowed when all applicable requirements above are met, and no other actions are permitted.
