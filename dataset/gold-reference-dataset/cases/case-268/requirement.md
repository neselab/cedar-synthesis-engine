Contract Lifecycle Access

These are the only permissions for users to execute, review, or sign contracts; each permission is sufficient only when all its stated requirements are met. Decisions use current recorded facts and trusted information supplied by the host application; they neither change contract state nor establish an order of activities. Amounts in the supplied records are stored in whole US cents. All times are UTC.

Execution
A user with the contract administrator role may execute a contract only when its value is at least $0.00, its status is signed, and its effective date is no later than the request’s current date. If its value exceeds $100,000.00, the host application must also confirm completion of the additional review.

Review
A user with the reviewer role may review a contract only when its value is at least $0.00 and its status is draft. The request’s current date and time must be at or after the request’s scheduled review start and strictly before its scheduled review end.

Signing
A user with the signatory or contract administrator role may sign a contract only when its value is at least $0.00 and both the user’s signing authority and the contract’s required authority are each one of 0, 1, or 2. If the contract value exceeds $1,000,000.00, the user’s signing authority must be at least the contract’s required authority, unless escalation has been approved and the user holds the signatory role. This exception waives only the authority comparison; all other signing requirements still apply. At values of $1,000,000.00 or less, no authority comparison is required.
