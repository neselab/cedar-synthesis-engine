Cloud Resource Deletion

A user may delete a cloud resource only if the user holds the owner role, the org administrator role, or both, and is also the resource’s recorded owner. The resource must not be in the prod environment. The user’s membership group must be the same hierarchy node as, or a descendant of, the resource’s organizational unit, and the request’s source IP address must be within 10.0.0.0/8.

These are the only permissions: allow deletion only when all these requirements hold under the current recorded facts and trusted request context, and deny all other requests, including requests for unlisted actions.
