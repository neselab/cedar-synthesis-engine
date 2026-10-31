Work Order Release and Signoff

A user with the inspector role, the quality manager role, or both may release a work order to production only when its defect count is between 0 and 100 inclusive, its status is inspected, its hold flag is false, and its part code begins with “SAFETY-”.

A user with the inspector role, the quality manager role, or both may sign off a work order only when its defect count is between 0 and 100 inclusive, the user is not the work order’s operator, and the request is made on the plant network.

These are the only permissions, and each permits its activity whenever all its stated requirements are met. Decisions use current recorded facts; these permissions do not change work order states or require either activity to precede the other.
