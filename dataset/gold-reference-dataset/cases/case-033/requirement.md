Actuator Setpoint Access

A user may adjust an actuator setpoint only if they hold at least one of the zone controller, maintenance tech, or facility manager roles; the actuator is online and has the “managed” device tag; and the user’s membership group is the same as, or descends from, the actuator’s zone group. The request must be made on the site network.

The request’s current time must be at or after its scheduled start time and strictly before its scheduled end time. All times are UTC. These are the only permissions: setpoint adjustment is allowed only when all these requirements are met, and no other actions are authorized.
