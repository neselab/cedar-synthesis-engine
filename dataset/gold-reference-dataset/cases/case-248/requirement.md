Contract Lifecycle Access

These are the only permissions: a user may execute, review, or sign a contract if and only if all conditions for that activity below are met, based on current recorded facts. These permissions do not change records or establish an order of activities. Users may hold multiple roles. Amounts in the supplied records are stored in whole US cents.

A user with the contract administrator role may execute a contract whose value is at least $0.00 and whose status is signed. If the value exceeds $10,000.00, the host application must also confirm completion of the additional review.

A user with the reviewer role may review a contract whose value is at least $0.00. If the value exceeds $1,000,000.00, the user must also be someone other than the contract’s drafter.

A user with the signatory role or the contract administrator role may sign a contract whose value is at least $0.00, provided that the user’s signing authority and the contract’s required authority are each one of 0, 1, or 2. If the value exceeds $1,000,000.00, the user’s signing authority must also be at least the contract’s required authority.
