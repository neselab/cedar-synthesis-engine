---
pattern: tag-based access with containsAny
difficulty: medium
features:
  - Set<String> attributes on both principal and resource
  - ".containsAny()" set operation (first use in benchmark)
  - ".containsAll()" for elevated access
  - intersection-based access decision
domain: content management / tagging
synthesis_difficulty: 2
---

# Set ContainsAny — Policy Specification

## Context

A tag-based content access system. Users have a set of "interest tags"
(strings) and a set of "clearance tags." Documents have a set of "topic
tags" and a set of "required clearance tags."

This scenario specifically exercises Cedar's `.containsAny()` set
operation, which tests whether two sets have a non-empty intersection.
This is the last remaining set operation not tested elsewhere in the
benchmark (`.contains()` and `.containsAll()` are exercised in other
scenarios).

## Requirements

### 1. Read Access — Tag Overlap

A User may `read` a Document when:
- The User's `interestTags` has ANY overlap with the document's
  `topicTags` (i.e. `principal.interestTags.containsAny(resource.topicTags)`),
  AND
- If the document has required clearance tags, the user's
  `clearanceTags` must contain ALL of them
  (`principal.clearanceTags.containsAll(resource.requiredClearanceTags)`).

### 2. Write Access — Full Tag Coverage

A User may `write` a Document when:
- The User's `interestTags` contain ALL of the document's `topicTags`
  (`principal.interestTags.containsAll(resource.topicTags)`), AND
- The User's `clearanceTags` contain ALL of the document's required
  clearance tags.

This is a stricter requirement: the user must be an expert in ALL the
document's topics, not just share any interest.

### 3. Tag Access — Manage Tags

A User may `manageTags` on a Document when:
- The User is the document's owner (`principal == resource.owner`).

Only owners can modify a document's tags.

### 4. Default Deny
All other requests are denied.
