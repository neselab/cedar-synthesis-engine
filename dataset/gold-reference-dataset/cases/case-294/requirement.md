Contract Lifecycle Access

These are the only permissions: users may execute, review, or sign contract records only when all conditions for the relevant activity below are met. Decisions use current recorded facts and trusted information supplied by the host application; these permissions neither change records nor require an order between activities. Amounts in the supplied records are stored in whole US cents.

A user with the contract administrator role may execute a contract when its value is at least $0.00, its status is signed, and the request is on the corporate network. If its value exceeds $10,000.00, the host application must also confirm completion of the additional review.

A user with the reviewer role may review a contract when its value is at least $0.00 and the request is on the corporate network. If its value exceeds $100,000.00, the user must not be the contract’s drafter.

A user with the signatory or contract administrator role may sign a contract when its value is at least $0.00 and both the user’s signing authority and the contract’s required authority are levels 0, 1, or 2. Only when the value exceeds $1,000,000.00 must the user’s signing authority meet or exceed the contract’s required authority, unless the host application confirms that escalation has been approved and the user has the signatory role. That exception waives only the authority comparison; all other signing requirements still apply.
