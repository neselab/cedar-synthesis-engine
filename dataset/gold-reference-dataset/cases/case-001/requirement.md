Contract Lifecycle Access

These are the only permissions for users to execute, review, or sign contracts; each permission requires all conditions stated for that activity, based on current recorded facts. Users may hold multiple roles. These permissions neither change contract states nor require an order of activities. Amounts in the supplied records are stored in whole US cents.

A user with the contract administrator role may execute a contract only when its value is at least $0.00, its status is signed, and the request is on the corporate network. If its value exceeds $100,000.00, the host application must also confirm completion of the additional review.

A user with the reviewer role may review a contract only when its value is at least $0.00 and its status is draft. If its value exceeds $100,000.00, the reviewer must not be the contract's drafter.

A user with the signatory or contract administrator role may sign a contract only when its value is at least $0.00, both the user's signing authority and the contract's required authority are levels 0, 1, or 2, and the user's authority is at least the required authority. The user must have used multi-factor authentication, and the contract's counterparty must not be among the user's conflicted counterparties.
