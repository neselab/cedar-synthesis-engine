Warehouse Zone Access and Order Picking

A user may access a warehouse zone only if the user holds the zone supervisor role, the zone is not locked, and the user’s clearance is at least the zone’s sensitivity. Both clearance and sensitivity must be one of 0, 1, 2, or 3.

A user may pick an order only if the user holds the picker or forklift operator role, the order’s item count is nonnegative, its status is released, and its items include CONTROLLED-002. If the item count exceeds 50, the host application must also confirm completion of the additional review.

These are the only permissions: each activity is permitted when all its stated requirements are met, and all other requests are denied. Decisions use current recorded facts and trusted information supplied by the host application; these permissions neither change records nor require either activity to precede the other.
