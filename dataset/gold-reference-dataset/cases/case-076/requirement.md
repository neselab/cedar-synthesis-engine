Contract Lifecycle Access

These are the only permissions: users may execute, review, or sign contracts only when all applicable requirements below are met, based on current recorded facts and trusted information supplied by the host application. Users may hold multiple roles. These permissions neither change contract records nor prescribe an order of activities. Source monetary values are recorded in US cents; dollar amounts are used below. All times are UTC.

Execution
A user with the contract administrator role may execute a contract only if its value is at least $0.00, its status is signed, and its effective date is no later than the current date supplied with the request. If its value exceeds $1,000,000.00, the host application must also confirm completion of the additional review.

Review
A user with the reviewer role may review a contract only if its value is at least $0.00 and the user is not its drafter. The current time supplied with the request must be at or after the request’s scheduled review start and strictly before its scheduled review end. The contract’s counterparty must not be among the user’s recorded conflicted counterparties.

Signing
A user with the signatory or contract administrator role may sign a contract only if its value is at least $0.00, both the user’s signing authority and the contract’s required authority are each one of the levels 0, 1, or 2, and the user is not the contract’s reviewer. If its value exceeds $100,000.00, the user’s signing authority must also be at least the contract’s required authority.

Amounts in the supplied records are stored in whole US cents.
