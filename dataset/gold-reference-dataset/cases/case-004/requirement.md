Cloud Resource Modification

A user may modify a cloud resource only if the user holds at least one of the owner, developer, or operator roles. The request’s recorded session age must be between 0 and 604,800, inclusive, and must also be no greater than 1,800.

The resource must carry the “production” tag. If its environment is “prod”, it must also be marked as promoted; resources in other environments do not require promotion. The request’s source IP address must be within 192.168.0.0/16.

These are the only permissions: modification is permitted only when all these requirements are met, and no other actions are permitted under this requirement.
