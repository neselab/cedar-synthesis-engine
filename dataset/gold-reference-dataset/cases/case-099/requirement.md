Marketplace Payout Access

A user may approve a payout only if they hold the finance approver role, the payout account’s KYC tier is 0, 1, 2, or 3, the payout amount is at least $0.00, and its status is requested. The request must come from the trusted network, and the current time must be at or after the request’s scheduled approval start time and strictly before its scheduled approval end time. All times are UTC.

A user may disburse a payout only if they hold the payout agent role, the payout account’s KYC tier is 2 or 3, the account’s fraud status is clear, and the payout amount is at least $0.00. If the amount exceeds $500.00, the host application must also confirm completion of the additional review; this review requirement does not apply to amounts of $500.00 or less. Amounts in the supplied records are stored in whole US cents.

These are the only permissions: each activity is permitted if and only if all its stated requirements hold for the user and payout, and no other activities are authorized. Users may hold multiple roles. These permissions use current recorded facts; they neither change payout state nor require an execution order between approval and disbursement.
