Applying Workload Manifests

A user may apply a workload manifest only if they hold at least one of the deployer, maintainer, or cluster operator roles. The workload must have a replica count of at least 0 and include the label "external". The user's membership group must be the same as, or descend from, the workload namespace's team group, and the request must originate from an IP address within 10.0.0.0/8.

If the workload's environment is "prod", its namespace must be promoted, unless the request is marked as an emergency change and the user holds the cluster operator role. This exception waives only the promotion requirement; all other requirements still apply.

These are the only permissions: applying a workload manifest is permitted only under all applicable conditions above, and no other actions are permitted.
