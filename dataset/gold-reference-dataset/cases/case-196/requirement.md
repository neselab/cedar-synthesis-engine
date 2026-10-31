Shipment Dispatch Authorization

A user may dispatch a shipment only if the user holds the driver or dispatch manager role, the shipment has a piece count of at least 0, and its tracking code begins with “CARRIER-B-”. If the piece count exceeds 100, the user must hold the dispatch manager role.

The user must not be the shipment’s planner unless expedite has been declared and the user holds the dispatch manager role. This exception waives only the requirement that the user differ from the planner; all other requirements still apply.

These are the only permissions granted: dispatch is permitted if and only if all applicable requirements above are met, and no other action is permitted.
