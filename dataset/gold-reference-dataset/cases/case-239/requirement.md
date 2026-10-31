Execution of Grid Switching Orders

A user may execute a switching order only if they hold the operator or control room operator role, are not the order’s planner, and the order’s circuit count is nonnegative. If the circuit count exceeds 1, the user must hold the control room operator role.

The user’s assigned code pattern must be exactly “FEEDER-B-*”, and the order’s feeder must begin with “FEEDER-B-”, followed by any suffix, including an empty suffix. The request must originate on the SCADA network, and its current time must be at or after the order’s scheduled start and strictly before its scheduled end. Times are UTC.

These are the only permissions: execution is allowed if and only if all the applicable requirements above are met, and no other activity is permitted under this requirement.
