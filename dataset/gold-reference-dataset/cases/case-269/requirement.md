Contract Lifecycle Access

These are the only permissions for users to execute, review, or sign contracts, and each is sufficient only when all its stated requirements are met using current recorded facts. These permissions do not change contract status or require an order of activities. Amounts in the supplied records are stored in whole US cents.

A user with the contract administrator role may execute a contract only if its value is at least $0.00, its status is signed, and the request is made on the corporate network. If the contract value exceeds $1,000,000.00, the host application must also confirm completion of the additional review; that confirmation is not required at or below $1,000,000.00.

A user with the reviewer role may review a contract only if its value is at least $0.00, its status is draft, and the user is not the contract’s drafter.

A user with the signatory role or the contract administrator role may sign a contract only if its value is at least $0.00 and both the user’s signing authority and the contract’s required authority are each one of the levels 0, 1, or 2. The user’s signing authority must be at least the contract’s required authority unless escalation has been approved and the user has the signatory role. This exception waives only the authority comparison; the permitted authority levels and all other signing requirements still apply.
