Contract Lifecycle Access

These are the only permissions for users to execute, review, or sign contracts; all applicable requirements below must be met using current recorded facts. These permissions neither change contract state nor establish an order between activities. Amounts in the supplied records are stored in whole US cents.

A user may execute a contract only if the user holds the contract administrator role, the contract value is at least $0.00, and the contract has signed status. If the contract value exceeds $1,000,000.00, the host application must also confirm that the additional review is complete.

A user may review a contract only if the user holds the reviewer role, the contract value is at least $0.00, and the user is not the contract’s drafter. The request’s current date and time must be at or after its scheduled review start and strictly before its scheduled review end, using UTC. The contract’s counterparty must not be among the user’s conflicted counterparties.

A user may sign a contract only if the user holds the signatory role; holding contract administrator alone is insufficient. The user’s signing authority and the contract’s required authority must each be one of 0, 1, or 2, and the contract value must be at least $0.00. The user must not be the contract’s reviewer and must have used multi-factor authentication.
