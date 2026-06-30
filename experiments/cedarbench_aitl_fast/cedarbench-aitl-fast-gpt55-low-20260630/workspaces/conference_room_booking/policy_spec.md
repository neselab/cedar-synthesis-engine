---
pattern: conference room booking (time-windowed exclusive resource)
difficulty: medium
features:
  - datetime comparison for booking window
  - capacity-based access (room size vs group size)
  - role-based priority booking
domain: workplace SaaS
synthesis_difficulty: 2
---

# Conference Room Booking — Policy Specification

## Context

A workplace booking system where `Employee` principals reserve
`Room` resources. Rooms have a `capacity` (Long) and a
`minBookingLevel` (Long, 1=anyone, 2=manager, 3=executive). The
request context carries the `groupSize` and `bookingStart`/`bookingEnd`
datetimes.

## Requirements

### 1. Book — Capacity + Level + Valid Window
An Employee may `book` a Room when:
- The employee's `level` is >= the room's `minBookingLevel`, AND
- The `context.groupSize` <= `resource.capacity`, AND
- The booking is in the future: `context.bookingStart > context.now`.

### 2. Cancel — Own Bookings
An Employee may `cancel` a Room booking. (No additional restrictions
beyond being an Employee — the host app checks booking ownership.)

### 3. View — All Employees
An Employee may `view` any Room's availability schedule.

### 4. Default Deny
All other requests are denied.
