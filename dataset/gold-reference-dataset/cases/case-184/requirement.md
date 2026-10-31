Work Order Release and Signoff

A user with the inspector or quality manager role may release a work order to production only when its status is inspected, its defect count is between 0 and 100 inclusive, and its part code begins with “CONTROLLED-” (with any suffix, including no suffix). The request’s current time must be at or after its scheduled production-release start time and strictly before its scheduled production-release end time. All times are UTC.

A user with the inspector or quality manager role may sign off a work order only when its status is inprogress, its defect count is between 0 and 2 inclusive, and the request is on the plant network.

These are the only permissions, and each is sufficient only when all its stated requirements are met. Neither permission changes the work order’s state or requires the actions to occur in a particular order.
