Invoice Approval Access

A user may approve an invoice only if they hold the approver or finance manager role, the invoice amount and surcharge are each at least $0.00, and its line item count is nonnegative. Amounts in the supplied records are stored in whole US cents.

Approval is permitted only from 08:00 UTC inclusive to 18:00 UTC exclusive each day, based on the request’s current time, and only when the invoice’s cost center begins with the exact prefix “OPS-”. If the invoice has more than 5 line items or its amount exceeds $25,000.00, the approving user must not be the invoice’s creator; otherwise, that creator-separation duty does not apply.

These are the only permissions: invoice approval is allowed exactly when all applicable requirements above are met, and no other activity is authorized.
