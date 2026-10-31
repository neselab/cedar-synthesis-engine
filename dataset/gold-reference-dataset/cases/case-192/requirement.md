Artifact Signing

A user may sign an artifact only if the user holds the committer role and is the artifact’s recorded builder, the artifact’s build tags include “release”, and the request’s source IP address is within 172.16.0.0/12. The request’s current time must be at or after its scheduled signing start and strictly before its scheduled signing end. All times are UTC.

These are the only permissions: signing is permitted when all these conditions hold, and no other action is permitted under this requirement.
