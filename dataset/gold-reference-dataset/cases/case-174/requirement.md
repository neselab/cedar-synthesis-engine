Reading Namespace Secrets

A user may read a namespace secret only if the user holds at least one of the deployer, maintainer, cluster operator, or service account roles. The user's clearance and the secret's sensitivity must each be 0, 1, or 2, and the user's clearance must be at least the secret's sensitivity.

The secret must have active status, and the request's source IP address must be within 10.0.0.0/8. These are the only permissions: a request is allowed only when it is for a user to read a namespace secret and all of these requirements are met; all other requests are denied.
