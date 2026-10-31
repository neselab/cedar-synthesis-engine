Contract Lifecycle Access

These are the only permissions: a user may execute, review, or sign a contract if and only if all requirements for that activity below are met, based on current recorded facts and trusted information supplied by the host application. These permissions do not change records or require an order between activities. Amounts in the supplied records are stored in whole US cents.

A user with the contract administrator role may execute a contract only when its value is at least $0.00 and its status is signed. If its value exceeds $1,000,000.00, the host application must also confirm completion of the additional review; that confirmation is not required at or below $1,000,000.00.

A user with the reviewer role may review a contract only when its value is at least $0.00, the user is not the contract’s drafter, and the contract’s counterparty is not among the user’s conflicted counterparties.

A user with the signatory role or the contract administrator role may sign a contract only when its value is at least $0.00, both the user’s signing authority and the contract’s required authority are one of the levels 0, 1, or 2, and the user’s signing authority is at least the contract’s required authority. The user must not be the contract’s reviewer, and the contract’s counterparty must not be among the user’s conflicted counterparties. Users may hold multiple roles, but role membership alone does not establish whether a user is the contract’s drafter or reviewer.
