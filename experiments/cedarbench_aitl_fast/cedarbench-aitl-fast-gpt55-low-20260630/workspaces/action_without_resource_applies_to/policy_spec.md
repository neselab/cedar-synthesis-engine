---
pattern: action without resource appliesTo
difficulty: medium
features:
  - session-level actions (no real resource)
  - sentinel resource entity (Session)
  - mixed resourceful and resource-less actions
  - role-based exclusion ("guest")
  - boolean precondition (sessionActive)
domain: identity / session management
synthesis_difficulty: 3
---

# Action Without Resource appliesTo -- Session Management

## Context

This scenario tests the Cedar pattern for **session-level actions that have
no real resource being acted upon**. A user who logs in, logs out, or
refreshes their auth token is not touching a document, row, or object --
they are operating on their own session state.

Cedar's schema language, however, **REQUIRES every action to declare a
non-empty `resource:` list**. Both of these forms are rejected by the
schema validator:

```
action logout appliesTo {            // omitted `resource` -- INVALID
    principal: [User],
    context: {},
};

action logout appliesTo {            // empty `resource: []` -- INVALID
    principal: [User],
    resource: [],
    context: {},
};
```

The canonical workaround is to introduce a **sentinel `Session` entity**
whose only purpose is to satisfy the schema. The entity carries no
policy-relevant attributes, and policy conditions for these actions depend
**only on `principal`**, never on `resource`.

This scenario also includes one ordinary resourceful action (`viewProfile`
on a `Profile` entity) to demonstrate that resource-less and resourceful
actions coexist in the same schema.

## Entities

- **`User`** -- authenticated principal.
  - `role: String` -- e.g. `"guest"`, `"member"`, `"admin"`.
  - `sessionActive: Bool` -- whether the user currently holds an active
    session.

- **`Session`** -- sentinel resource for session-level actions. No
  attributes. Exists only so that login / logout / refreshToken can declare
  a non-empty `resource:` list in their `appliesTo`.

- **`Profile`** -- a real resource for the contrasting `viewProfile` case.
  - `owner: User` -- the profile's owner.

## Actions

- **`login`** (principal: User, resource: Session) -- start a session.
- **`logout`** (principal: User, resource: Session) -- end the current session.
- **`refreshToken`** (principal: User, resource: Session) -- renew the
  session's auth token.
- **`viewProfile`** (principal: User, resource: Profile) -- read a profile.

## Requirements

### Action: login

A login is permitted for **any** `User` on **any** `Session`, with no
preconditions. Login is the universal entry point and cannot itself depend
on session state (it is what *creates* the session).

- **Floor:** any User MUST be permitted to log in.

### Action: logout

A logout is permitted only when the principal currently has an active
session: `principal.sessionActive`. Logging out a user who is not logged
in is at best a no-op and at worst a sign of a confused client; deny it.

- **Floor:** any User with `sessionActive == true` MUST be permitted to
  log out.

### Action: refreshToken

Refreshing an auth token is permitted only when **both**:

1. The principal has an active session: `principal.sessionActive`.
2. The principal is not a guest: `principal.role != "guest"`.

Guest sessions do not get refreshed -- they expire on their stated lifetime
and the user must re-login.

- **Floor:** any active, non-guest User MUST be permitted to refresh.

### Action: viewProfile

The contrasting resourceful case. `viewProfile` is permitted only when
the principal owns the profile: `principal == resource.owner`.

- **Floor:** the profile owner MUST be permitted to view their own profile.

### Liveness

Each of the four actions must permit at least one request.

## Out of scope

- No multi-device session tracking.
- No token expiry / temporal attributes.
- No admin override (an admin cannot log out another user in this model;
  that would require a different action signature with a target principal
  in context).
- No global forbids.
