Folio Adjustment Access

These are the only permissions for users to approve or post folio adjustments, and each permission requires all applicable conditions below. Decisions use current recorded facts and trusted information supplied by the application; these permissions neither change records nor require an order between approval and posting. Amounts in the supplied records are stored in whole US cents.

Approval

A user with the accounting clerk or revenue manager role may approve a folio adjustment only when the adjustment amount and folio balance are each at least $0.00, the folio has adjustment_posted status, and the folio’s property region is the same hierarchy node as, or a descendant of, the user’s assigned group. If the adjustment amount exceeds $100.00, large credit approval must also have been recorded.

Posting

A user with the front desk agent or night auditor role may post a folio adjustment only when the user’s adjustment authority level and the folio’s guest segment are each one of 0, 1, 2, or 3, the adjustment amount and original charge are each at least $0.00, and the folio’s dispute category includes billing_error. If the original charge minus the adjustment amount exceeds $2,500.00, the user’s adjustment authority level must also be at least the folio’s guest segment.
