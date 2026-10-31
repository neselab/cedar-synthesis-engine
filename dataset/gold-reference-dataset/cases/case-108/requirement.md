Claim Approval and Payout Permissions

These are the only permissions: a user may approve a claim or issue a payout if and only if all requirements for that activity below are met. Decisions use current recorded facts and trusted request information; these permissions neither change records nor require an order between activities. Amounts in the supplied records are stored in whole US cents.

Claim approval

A user with the reviewer or claims manager role may approve a claim whose amount and deductible are each at least $0.00 and whose line item count is nonnegative. If the claim has more than 20 line items or its amount exceeds $10,000.00, the user must not be the claim’s handler.

Payout issuance

A user with the payout officer or claims manager role may issue a payout when the payout amount and the related claim’s amount and deductible are each at least $0.00, and the related claim’s line item count is nonnegative. If that claim has more than 20 line items, the user must not be its approver. The request’s current time must be at or after its scheduled payout start time and strictly before its scheduled payout end time, using UTC.
