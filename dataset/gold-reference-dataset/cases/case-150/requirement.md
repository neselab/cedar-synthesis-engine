Meter Data Management Access

These are the only permissions for adjusting meter readings and approving billing runs, and each is granted only when all applicable requirements below are met using current recorded facts. Amounts in the supplied records are stored in whole US cents.

A user with the meter reader or data steward role may adjust a reading for a meter account only when the account’s adjustment count is nonnegative, its last bill amount is at least $0.00, and the request is made on the corporate network. If the last bill amount exceeds $500.00, the user must also be different from the account’s last reader.

A user may approve a billing run only if they hold the billing manager role; the billing analyst role alone is insufficient. The user’s authority level and the billing run’s account tier must each be one of 0, 1, 2, or 3. The billing run must have a bill amount of at least $0.00, a rate between 0 and 100,000 inclusive, nonnegative usage, and submitted status. Its region must be the same hierarchy node as, or a descendant of, the user’s assigned group.
