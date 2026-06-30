---
pattern: file-path ACL / glob escape sequences
difficulty: medium
features:
  - like operator with literal-char escapes
  - glob wildcard vs regex distinction
  - role-gated path patterns
domain: file-storage / document-management systems
synthesis_difficulty: 3
---

# File-Path ACL with Literal Special Characters — Policy Specification

## Context

This policy implements a file-path access-control list. Access is
determined by pattern-matching the file's path against fixed string
patterns. Some legitimate file paths in the system contain literal
`*` characters in their names (a quirk of an upstream report-naming
convention), and the policy must distinguish those from arbitrary
wildcards in the patterns.

Principal is `User` with a `role: String` attribute (`"admin"` or
`"user"`). Resource is `File` with a `path: String` attribute. Two
actions: `read`, `write`.

## Requirements

### 1. Standard Document Read (All Users)
- Any User may `read` a File when the path matches the pattern
  `docs/*` — that is, the path begins with `docs/` and any sequence
  of zero or more characters may follow. Examples that qualify:
  `docs/intro.md`, `docs/`, `docs/sub/page.html`. Example that does
  not: `archive/docs/old.md`.

### 2. Final-Report Read (Standard Users)
- A User whose role is `"user"` may `read` a File when the path
  matches the pattern `reports/`-then-a-literal-asterisk-then-`-final`.
  That is: the path begins with `reports/`, followed by one literal
  `*` character, followed by `-final` (and nothing else). Examples
  that qualify: `reports/*-final` exactly, or — depending on how the
  pattern is written — paths containing the exact substring
  `reports/<anything>*-final` are NOT intended; this rule is meant to
  match paths where a literal `*` appears in the filename, such as
  `reports/Q1*-final` if and only if the policy's pattern allows
  arbitrary text between `reports/` and the literal `*`.

  To make the requirement unambiguous: the policy MUST use Cedar's
  escape sequence for a literal asterisk so that `*` in the pattern
  matches an actual `*` character in the path, NOT a wildcard. The
  intended permitted set is exactly: paths of the form
  `reports/<any chars>*-final` where the `*` is literal. For example,
  `reports/Q1*-final` and `reports/2025*-final` qualify;
  `reports/Q1-final` (no literal `*`) does NOT.

### 3. System File Read (Admins Only)
- A User whose role is `"admin"` may `read` a File when the path
  matches `system/*` — path begins with `system/` followed by any
  characters. Non-admin users MUST NOT read `system/*` files.

### 4. Admin Write (All Files)
- A User whose role is `"admin"` may `write` any File regardless of
  path. Non-admin users MUST NOT write any file.

## Notes
- Cedar has one string-matching primitive: the `like` operator, which
  uses glob-style patterns (not regex). The wildcard character is `*`
  and matches zero or more characters. Patterns are anchored — the
  whole string must match.
- A literal `*` in the target string is matched by an escape sequence
  in the pattern; refer to the Cedar documentation for the exact
  escape character. Do NOT use regex conventions (e.g. `.*`, `\\*`,
  `[*]`) — they will not parse or will not behave as intended.
- Cedar strings have no `.contains()`, `.startsWith()`, or
  `.endsWith()` methods. Pattern-matching MUST go through `like`.
