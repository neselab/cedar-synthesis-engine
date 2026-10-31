Grid Switching Order Access

A user may authorize a switching order only if the user holds the planner or shift supervisor role, is not the order’s recorded executor, and has the assigned code pattern exactly “FEEDER-A-*”. The order must be in planned status, its voltage level must be 0, 1, 2, or 3, and its feeder must match “FEEDER-A-*”, meaning it begins with “FEEDER-A-” followed by any suffix, including an empty suffix.

A user may execute a switching order only if the user holds the operator or control room operator role and the order is in authorized status with a nonnegative circuit count. The request’s current time must be at or after the scheduled start and strictly before the scheduled end. If the circuit count exceeds 10, the user must hold the control room operator role; all other execution requirements still apply. Times are UTC.

These are the only permissions: each activity is permitted if and only if all its stated requirements hold for a user and a switching order, and no other activities are permitted. Decisions use current recorded facts and the trusted request context; these permissions neither change order status nor establish an execution sequence between activities.
