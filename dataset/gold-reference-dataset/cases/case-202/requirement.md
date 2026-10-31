Work Order Signoff

A user may sign off a work order only if they hold the inspector role, the quality manager role, or both. The work order must have a defect count of 0 or 1, and its part code must begin with “CONTROLLED-”.

The user must not be the work order’s operator unless the deviation is authorized and the user holds the quality manager role. This exception waives only the restriction on signing off one’s own work as operator; all other requirements still apply. The request’s current time must be at or after its scheduled signoff start and strictly before its scheduled signoff end. All times are UTC.

These are the only permissions granted by this requirement.
