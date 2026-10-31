Work Order Signoff

A user may sign off a work order only if the user holds the inspector or quality manager role, the work order has exactly zero defects, its status is inprogress, and its part code begins with “CONTROLLED-”.

The current time supplied with the request must be at or after the scheduled signoff start time and strictly before the scheduled signoff end time. All times are UTC. These are the only permissions: signoff is allowed when all these requirements are met, and no other actions are authorized by this requirement.
