Contract Lifecycle Access

These are the only permissions for users to execute, review, or sign contracts; each permission is sufficient only when all of its stated requirements hold, based on current recorded facts. These permissions neither change contract states nor prescribe an order of activities. Amounts in the supplied records are stored in whole US cents.

A user with the contract administrator role may execute a contract only if its value is at least $0.00, its status is signed, and the request is made on the corporate network. If the contract value exceeds $1,000,000.00, the host application must also confirm completion of the additional review.

A user with the reviewer role may review a contract only if its value is at least $0.00. If the value exceeds $10,000.00, the user must also be different from the contract’s drafter.

A user with the signatory role or the contract administrator role may sign a contract only if its value is at least $0.00, the user is different from the contract’s reviewer, and the user has used multi-factor authentication. Both the user’s signing authority and the contract’s required authority must be one of the levels 0, 1, or 2, and the user’s signing authority must be at least the contract’s required authority.
