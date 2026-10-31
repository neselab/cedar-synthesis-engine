Service Account Token Revocation

A user may revoke a service account token only if the user holds the cluster operator role and is the token’s issuer. The current request time must be strictly earlier than the token’s expiration time, and the user must have used multi-factor authentication. The user’s group must be the same as, or descend from, the team group of the namespace to which the token is bound. The request’s source IP address must be within 172.16.0.0/12.

These are the only permissions: revocation is permitted when all these requirements are met, and no other actions are permitted under this requirement.
