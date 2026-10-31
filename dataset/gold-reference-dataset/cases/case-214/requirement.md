Claim Approval and Payout Permissions

A user may approve a claim only if they hold the reviewer or claims manager role, are not the claim’s handler, and the claim is not on fraud hold. The claim amount and deductible must each be at least $0.00, the line item count must be at least zero, and the claim code must begin with “LIABILITY-”, followed by any sequence of characters, including none.

A user may issue a payout only if they hold the payout officer or claims manager role. The payout amount and the associated claim’s amount and deductible must each be at least $0.00, and that claim’s line item count must be at least zero. The associated claim code must begin with “PROPERTY-”, followed by any sequence of characters, including none. If the associated claim has more than 5 line items, the user must not be that claim’s approver; this separation requirement does not apply when the count is 5 or fewer.

Amounts in the supplied records are stored in whole US cents. These are the only permissions: each activity is permitted exactly when all its stated requirements hold, and no other activities are authorized. These permissions neither change records nor require an execution order between approval and payout.
