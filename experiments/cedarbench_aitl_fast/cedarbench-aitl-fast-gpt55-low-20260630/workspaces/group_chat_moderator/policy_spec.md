---
pattern: group chat moderator hierarchy
difficulty: medium
features:
  - entity membership (User in Channel)
  - set contains for moderator list
  - owner vs moderator vs member permission split
domain: social / messaging (Discord/Slack)
synthesis_difficulty: 5
---

# Group Chat Moderator — Policy Specification

## Context

A messaging platform where `User` principals interact with `Channel`
resources. Channels have an `owner` (User), a `moderators` set
(Set<User>), and an `isArchived` boolean.

This scenario tests the common Discord/Slack moderation pattern:
owners have full control, moderators can manage messages, members
can read and post, non-members are excluded.

## Requirements

### 1. Read — Members Only
A User may `read` a Channel when:
- The user is a member of the channel (`resource.members.contains(principal)`), AND
- The channel is not archived.

### 2. Post — Members, Not Archived
A User may `post` to a Channel when:
- The user is a member of the channel, AND
- The channel is not archived.

### 3. Delete Message — Moderators or Owner
A User may `deleteMessage` in a Channel when:
- The user is the channel's owner (`principal == resource.owner`), OR
- The user is in the channel's moderator set
  (`resource.moderators.contains(principal)`).

Moderators and owners can delete messages even in archived channels
(for cleanup).

### 4. Pin — Moderators or Owner
A User may `pin` in a Channel when:
- The user is the channel's owner, OR
- The user is in the moderator set.

### 5. Archive — Owner Only
A User may `archive` a Channel when:
- The user is the channel's owner.

### 6. Default Deny
All other requests are denied. Non-members cannot read or post.
Regular members cannot delete others' messages or archive.
