Warehouse Fulfillment Access

A user may access a warehouse zone only if the user holds the zone supervisor role, the user’s clearance and the zone’s sensitivity are each one of 0, 1, 2, or 3, the clearance is at least the sensitivity, and the zone is not locked. No additional picker or forklift operator role is required for zone access.

A user may pick an order only if the user holds the picker or forklift operator role, the order has a nonnegative item count, its status is released, and its items include RESTRICTED-003. The user’s assigned code pattern must be exactly WAVE-B-*, and the order’s pick list code must start with WAVE-B-, followed by any sequence of characters, including no characters.

These are the only permissions: each activity is permitted if and only if all its stated requirements hold. They neither change records nor require one activity to precede the other.
