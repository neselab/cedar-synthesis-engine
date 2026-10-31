Cloud Resource Modification

A user may modify a cloud resource only if they hold at least one of the owner, developer, or operator roles, have used multi-factor authentication, and make the request from an IP address within 172.16.0.0/12. The request’s session age must be between 0 and 604,800, inclusive; the source does not specify the unit for session age.

The resource must have the “sensitive” tag. If its environment is “prod”, it must also be marked as promoted; other environments do not require promotion. These are the only permissions: modification is allowed exactly when all these requirements are met, and no other actions are permitted under this requirement.
