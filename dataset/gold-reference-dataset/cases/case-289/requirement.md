Contract lifecycle access

These are the only permissions for users to execute, review, or sign contracts; each permission requires all conditions stated for that activity. Users may hold multiple roles. Amounts in the supplied records are stored in whole US cents. These permissions use current recorded facts and neither change contract state nor require an order between activities.

A user with the contract administrator role may execute a contract only if its value is at least $0.00, its status is signed, and the request is made on the corporate network. If the contract value exceeds $1,000,000.00, the host application must also confirm completion of the additional review.

A user with the reviewer role may review a contract only if its value is at least $0.00 and the user is not its drafter. The request’s current date and time must be at or after its scheduled review start and strictly before its scheduled review end. These times are UTC.

A user with the signatory or contract administrator role may sign a contract only if its value is at least $0.00, both the user’s signing authority and the contract’s required authority are one of 0, 1, or 2, and the user has used multi-factor authentication. The user’s signing authority must be at least the contract’s required authority unless escalation has been approved and the user has the signatory role. This exception waives only the authority comparison; all other signing requirements still apply.
