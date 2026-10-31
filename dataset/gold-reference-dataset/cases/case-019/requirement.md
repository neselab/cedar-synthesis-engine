Deployment Approval and Promotion

A user may approve a deployment only if the user holds the approver or release manager role, the deployment’s change risk is between 0 and 100 inclusive, and the request originates from an IP address within 192.168.0.0/16. The user must not be the deployment’s committer unless the request is marked as an emergency change and the user holds the release manager role. This exception waives only the requirement to differ from the committer; all other approval requirements still apply.

A user may promote a deployment only if the user holds the release manager role, the user’s deploy tier is 0, 1, or 2, and the deployment’s target environment is 0, 1, or 2. The deployment must have approved status, the user must be its recorded approver, and the request must originate from an IP address within 172.16.0.0/12.

These are the only permissions: each activity is permitted when all its applicable requirements are met, and no other activities are permitted. These permissions neither change deployment state nor prescribe an order of execution.
