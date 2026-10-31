Reading Namespace Secrets

A user may read a namespace secret only if they hold at least one of the deployer, maintainer, cluster operator, or service account roles, their clearance is 0, 1, or 2, and the secret’s sensitivity is 0, 1, or 2. The secret must be active, the user must own it, and the user must be a member of its namespace.

The presented token must name the requesting user as its subject and be bound to the secret’s namespace. The current time must be strictly earlier than the token’s expiration time, and the user must have used multi-factor authentication. These requirements together are the only permissions for reading namespace secrets; requests that do not meet them and requests for any other action must be denied.
