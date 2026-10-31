Number Porting Access

A user may authorize a number port request only if they hold the porting specialist or porting supervisor role, the request has a nonnegative number block size and validated status, and the user is on the carrier network. The current time must be at or after the supplied authorization scheduled start and strictly before the supplied authorization scheduled end. Times are UTC.

A user may complete a number port request only if they hold the line technician or porting supervisor role, the request has a nonnegative number block size, and they are the request’s assigned technician. The user’s assigned code pattern must be exactly “WHOLESALE-*”, and the request’s carrier code must begin with “WHOLESALE-”, followed by any suffix, including an empty suffix. If the number block size exceeds 10, the user must also hold the porting supervisor role.

These are the only permissions: each operation is permitted exactly when all its stated requirements are met. These permissions neither change records nor require an execution order between the operations.
