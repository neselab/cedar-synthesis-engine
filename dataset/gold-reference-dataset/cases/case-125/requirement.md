Shipment Dispatch Authorization

A user may dispatch a shipment only if the user holds the driver or dispatch manager role, the shipment has a nonnegative piece count and a status of created, and the current request time is strictly earlier than the shipment’s delivery window end. Times are in UTC.

The shipment’s hazmat classes must include “corrosive,” and its tracking code must begin with “CARRIER-A-”, followed by zero or more characters. If the piece count exceeds 10, the user must hold the dispatch manager role; for counts from 0 through 10 inclusive, either qualifying role is sufficient, subject to all other requirements.

These are the only permissions for dispatching shipments, and no other actions are permitted under this requirement.
