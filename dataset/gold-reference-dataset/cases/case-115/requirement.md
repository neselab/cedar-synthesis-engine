Meter Data Management Access

These are the only permissions: a user may adjust a meter reading or approve a billing run if and only if all requirements for that activity below are met. Decisions use current recorded facts; these permissions neither change records nor require the activities to occur in any order. Amounts in the supplied records are stored in whole US cents.

Adjusting a meter reading

A user with the meter reader or data steward role may adjust a reading on a meter account only when the account’s adjustment count is nonnegative, its last bill amount is at least $0.00, and its rate classes include “regulated_residential”. If the adjustment count exceeds 1, the user must differ from the account’s last reader.

Approving a billing run

A user with the billing analyst or billing manager role may approve a billing run only when the user’s authority level and the run’s account tier are each one of 0, 1, 2, or 3; the bill amount is at least $0.00; the rate is between 0 and 100,000, inclusive; and usage is nonnegative. The run’s region must be the same hierarchy node as, or a descendant of, the user’s assigned group. If the bill amount exceeds $500.00, the user’s authority level must also be at least the run’s account tier.
