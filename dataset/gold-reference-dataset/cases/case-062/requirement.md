Cloud Resource Deletion

A user may delete a cloud resource only if they hold the owner or org administrator role, have used multi-factor authentication for the request, and belong to a group that is the same as or descends from the resource’s organizational unit. The request’s source IP address must be within 172.16.0.0/12.

The resource must not be in the prod environment unless its temporary grant flag is true and the user holds the owner or org administrator role. This exception waives only the restriction on deleting production resources; all other requirements still apply.

These are the only permissions: deletion is allowed when all applicable requirements above are met, and no other actions are permitted under this requirement.
