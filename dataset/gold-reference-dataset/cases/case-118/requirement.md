Order Picking Access

A user may pick an order only if the user holds the picker role, the forklift operator role, or both; the order is released; its item count is nonnegative; and its items include RESTRICTED-003. The host application must confirm that the user’s on-site badge flag is true. The current request time must be at or after the request’s scheduled picking start and strictly before its scheduled picking end. All times are UTC.

When the order’s item count exceeds 200, the host application must also confirm completion of the additional review. This review requirement does not apply to orders with 200 or fewer items; all other requirements still apply.

These are the only permissions: order picking is allowed only when all applicable requirements above are met, and no other action is authorized.
