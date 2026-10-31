Grid Switching Order Access

A user with the planner or shift supervisor role may authorize a switching order only when its voltage level is 0, 1, 2, or 3, its status is planned, lockout tagout has been verified, and the request is on the SCADA network.

A user with the operator or control room operator role may execute a switching order only when its circuit count is nonnegative, the user is not the order’s planner, and the request is on the SCADA network.

These are the only permissions: each activity is permitted when all of its stated requirements are met. Users may hold multiple roles. These permissions neither change the order’s state nor require the activities to occur in a particular sequence.
