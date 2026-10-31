Cloud Resource Modification

A user may modify a cloud resource only if the user holds at least one of the owner, developer, or operator roles and the user's membership group is the same as, or descends from, the resource's organizational group. The resource must have the “managed” tag. If its environment is prod, it must also be marked as promoted; other environments do not require promotion.

The request's recorded session age must be between 0 and 604,800, inclusive, and must also be at most 3,600. The request's source IP address must fall within 192.168.0.0/16. These are the only permissions: modification is allowed if and only if all these requirements are met, and no other action is permitted under this requirement.
