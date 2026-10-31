Grid Switching Order Access

A user may authorize a switching order only if they hold the planner or shift supervisor role, the order’s voltage level is 0, 1, 2, or 3, they are not the order’s recorded executor, and the request is made on the SCADA network. For voltage levels 2 and 3, the user must hold the shift supervisor role.

A user may execute a switching order only if they hold the operator or control room operator role and the order’s circuit count is nonnegative. The order must have authorized status unless an outage emergency has been declared and the user holds the control room operator role. This exception waives only the authorized-status requirement; all other execution requirements still apply. If the circuit count exceeds 3, the user must hold the control room operator role.

These are the only permissions, and each is sufficient only when all its applicable requirements are met. They rely on current recorded facts and do not change order state or require an execution sequence between the activities.
