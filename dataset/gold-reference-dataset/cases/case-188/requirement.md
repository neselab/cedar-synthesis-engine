Deployment Approval and Promotion Access

A user may approve a deployment only if they hold the release manager role, are not the deployment’s committer, and the deployment’s change risk is between 0 and 100, inclusive. The request must originate from an IP address within 172.16.0.0/12. Holding the approver role alone does not permit approval.

A user may promote a deployment only if they hold the release manager role, their deploy tier is 0, 1, or 2, and the deployment’s target environment is 0, 1, or 2. The deployment must have approved status, and the request must originate from an IP address within 10.0.0.0/8.

These are the only permissions: each activity is permitted when all its stated requirements are met, and all other requests are denied. These permissions do not change deployment state or require an execution order between the activities.
