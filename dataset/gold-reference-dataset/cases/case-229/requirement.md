Zone Schedule Override

A user may override a zone schedule only if the user holds the facility manager role, is the zone’s recorded controller, and the request indicates that occupancy is detected. Holding the zone controller role alone is insufficient. The user’s control tier and the zone’s criticality must each be 0, 1, or 2, and the control tier must be at least the criticality.

These are the only permissions: allow a zone schedule override when all these requirements hold, and deny all other requests.
