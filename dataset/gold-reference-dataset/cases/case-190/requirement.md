Zone Schedule Override

A user may override a zone schedule only if they hold the zone controller or facility manager role and are the zone’s recorded controller. The user’s control tier and the zone’s criticality must each be 0, 1, or 2, and the user’s control tier must be at least the zone’s criticality.

The zone must have scheduled status, and occupancy must be detected for the request. The request’s current time must be at or after its scheduled override start and strictly before its scheduled override end. All times are UTC.

These are the only permissions: a zone schedule override is permitted if and only if all these requirements are met; no other actions are permitted.
