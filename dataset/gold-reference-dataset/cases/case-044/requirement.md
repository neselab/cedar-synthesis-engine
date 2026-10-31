Applying Workload Manifests

A user may apply a workload manifest only if they hold at least one of the deployer, maintainer, or cluster operator roles, the workload has a nonnegative replica count and includes the label "external", the user's granted scope equals the workload's required verb, and the request's source IP address is within 172.16.0.0/12.

If the workload's replica count exceeds 50, the user must also be someone other than the workload's creator. These are the only permissions granted; no other actions are permitted.
