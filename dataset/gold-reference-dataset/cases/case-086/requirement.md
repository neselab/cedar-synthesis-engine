Meter Data Management Access

The following are the only permissions for adjusting meter readings and approving billing runs; a user may perform an activity if and only if all requirements for that activity are met. Amounts in the supplied records are stored in whole US cents.

Adjusting a meter reading
A user with the meter reader or data steward role may adjust a reading on a meter account whose adjustment count and last bill amount are both nonnegative. If the last bill amount exceeds $500.00, the user must differ from the account’s last reader.

Approving a billing run
A user with the billing analyst or billing manager role may approve a billing run when the user’s authority level and the run’s account tier are each one of 0, 1, 2, or 3; the run’s bill amount and usage are both nonnegative; and its rate is between 0 and 100,000, inclusive. The run’s region must be the same hierarchy node as, or descend from, the user’s assigned group. If the product of the run’s usage and rate exceeds 15,000, the user’s authority level must also be at least the run’s account tier.
