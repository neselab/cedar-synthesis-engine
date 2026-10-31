Contract Lifecycle Access

These are the only permissions: users may execute, review, or sign contracts if and only if all applicable requirements below are met. Every activity requires a contract value of at least $0.00. Amounts in the supplied records are stored in whole US cents. Decisions use current recorded facts and trusted information supplied by the host application; these permissions neither change contract states nor establish an order between activities.

A user may execute a contract only if the user holds the contract administrator role and the contract is in signed status. If the contract value exceeds $1,000,000.00, the host application must also confirm completion of the additional review.

A user may review a contract only if the user holds the reviewer role and the contract is in draft status. The request’s current date and time must be at or after its scheduled review start and strictly before its scheduled review end, using UTC.

A user may sign a contract only if the user holds the signatory role or the contract administrator role. The user’s signing authority and the contract’s required authority must each be one of 0, 1, or 2. If the contract value exceeds $10,000.00, the user’s signing authority must also be at least the contract’s required authority. The contract’s counterparty must not be among the user’s recorded conflicted counterparties.
