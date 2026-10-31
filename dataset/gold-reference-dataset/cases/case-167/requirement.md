Switching Order Authorization

A user may authorize a switching order only if they hold the planner or shift supervisor role and the order’s voltage level is 0, 1, 2, or 3. For voltage levels 1, 2, and 3, the user must hold the shift supervisor role.

The user must not be the order’s executor unless an outage emergency has been declared and the user holds the shift supervisor role. This exception waives only the requirement to be different from the executor; all other requirements still apply. The current request time must be at or after the order’s scheduled start and strictly before its scheduled end, with times interpreted in UTC. The request must be on the SCADA network.

These are the only permissions to authorize a switching order; no other actions are permitted under this requirement.
