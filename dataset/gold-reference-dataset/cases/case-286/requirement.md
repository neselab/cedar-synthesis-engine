Network Change Approval and Implementation

These are the only permissions for users to approve or implement network change requests, and each permission requires all applicable conditions below. Decisions use current recorded facts and trusted information from the host application; these permissions neither change records nor prescribe an order of execution. Amounts in the supplied records are stored in whole US cents.

Approval
A user may approve a change request only if they hold the change manager or cabapprover role. The user's authority level and the change's risk must each be one of 0, 1, 2, or 3, and the authority level must be at least the risk. The affected node count and rollback step count must each be nonnegative, and the estimated cost must be at least $0.00. If the affected node count plus the rollback step count exceeds 10, the host application must confirm completion of the additional review. If the estimated cost exceeds $10,000.00, the user must hold the cabapprover role.

Implementation
A user may implement a change request only if they hold the network engineer or senior engineer role, the affected node count is nonnegative, and the request's status is approved. Unless the change is marked as an emergency, the current time must be at or after the recorded maintenance window start and strictly less than four hours after that start, using UTC times. The emergency exception waives only this timing requirement; all other implementation requirements still apply.
