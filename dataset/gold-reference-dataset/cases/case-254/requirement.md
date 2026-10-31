Device Command Access

A user may send a command to a device only if the user holds at least one of the operator, technician, or fleet administrator roles, the device is active, its firmware tags include “beta,” and the request originates from an IP address within 192.168.0.0/16.

When the device is in maintenance mode, the request must also have maintenance-command authorization from the host application. When maintenance mode is off, that additional authorization is not required; all other requirements still apply. These are the only permissions granted by this requirement.
