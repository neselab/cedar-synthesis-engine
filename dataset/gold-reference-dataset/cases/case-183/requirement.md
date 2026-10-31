Applying a Workload Manifest

A user may apply a workload manifest only if they hold at least one of the deployer, maintainer, or cluster operator roles, are a member of the workload’s namespace, and make the request from a source IP address within 172.16.0.0/12. The workload must have the label "restricted" and a replica count of at least 0. If the replica count exceeds 3, the user must not be the workload’s creator.

These are the only permissions; no other actions are authorized.
