Cloud Resource Modification

A user may modify a cloud resource only if the user holds at least one of the owner, developer, or operator roles and is also the resource’s recorded owner. The request’s recorded session age must be between 0 and 604,800, inclusive, and must not exceed 900. The source IP address must be within 10.0.0.0/8.

The resource must carry the “production” tag. If its environment is prod, it must also be marked as promoted; promotion is not required for other environments. All other requirements still apply. These are the only permissions: requests that do not meet all applicable requirements, and requests for any other action, must be denied.
