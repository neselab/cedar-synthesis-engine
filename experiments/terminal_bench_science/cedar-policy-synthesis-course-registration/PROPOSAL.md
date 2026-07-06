# Terminal-Bench Science Proposal: Cedar Policy Synthesis From Authorization Intent

## One-Sentence Summary

This task evaluates whether terminal agents can turn realistic natural-language access-control requirements into a deployable Cedar policy store that passes deterministic symbolic verification checks.

## Proposal-Form Version

We propose a Terminal-Bench Science task in security-policy autoformalization. The agent is given realistic university course-registration access-control requirements and a Cedar authorization schema, then must produce `/app/policy.cedar`, a deployable Cedar policy store. The final artifact is graded by deterministic Cedar validation and symbolic verification checks over hidden floor, ceiling, and liveness properties.

This is a real engineering-science workflow: policy engineers and security researchers routinely translate organizational requirements into formal authorization policies, validate those policies, and repair them when verification exposes over-permission or under-permission. The task is difficult because a policy can compile and look plausible while still violating lifecycle, ownership, privacy, or role/action boundaries. Common mistakes include allowing students to modify another student's schedule, allowing registration after the registration window closes, exposing report cards to the wrong student, allowing professors to alter another professor's course offerings, or allowing non-professors to enter grades.

The verifier is outcome-based and programmatic. It does not inspect the agent's process or require matching a particular oracle solution. It accepts any Cedar policy denotation that satisfies the hidden semantic target. Broad policies fail ceiling checks; overly narrow policies fail floor or liveness checks. The oracle solution passes locally with Cedar CLI 4.10.0 and CVC5, and a deliberately overbroad `permit (principal, action, resource);` policy fails, showing that the task is not syntax-only.

## Proposed Category

- Domain: Engineering Sciences
- Field: Autoformalization / Security Policy Verification
- Task type: terminal-based formalization and verifier-guided repair

## Why This Fits Terminal-Bench Science

Terminal-Bench Science asks for real computational workflows that are objectively verifiable and difficult for current agents. This task is a compact formal-security workflow:

1. Read natural-language organizational authorization requirements.
2. Inspect a provided Cedar schema.
3. Write a Cedar policy store.
4. Use the terminal to run Cedar validation and repair syntax/type errors.
5. Pass hidden symbolic floor, ceiling, and liveness checks.

The task measures whether an agent can produce semantically correct formal artifacts, not merely plausible prose or syntactically valid code.

This sits naturally under `other-sciences / engineering-sciences / autoformalization`. It is not a natural-science simulation task, but TB-Science explicitly includes mathematical sciences, autoformalization, engineering sciences, scientific computing, and interdisciplinary computational workflows.

## What The Agent Sees

The agent receives:

- `requirements.md`: course-registration access-control requirements.
- `schema.cedarschema`: the application authorization schema.
- `policy.cedar`: an empty starter file.
- `instruction.md`: task directions.

The agent must produce `/app/policy.cedar`.

## What The Hidden Verifier Checks

The verifier runs:

1. `cedar validate --schema schema.cedarschema --policies policy.cedar`
2. Symbolic ceiling checks for over-permission.
3. Symbolic floor checks for required access.
4. Liveness checks to ensure required workflows are not empty.

The checks accept any policy denotation that satisfies the intended behavior. They do not require matching the oracle solution's syntax.

## Why It Is Hard

Common plausible failures include:

- permitting students to modify someone else's schedule;
- permitting registration after the registration window closes;
- permitting students to view another student's report card;
- permitting professors to modify another professor's course offerings;
- permitting non-professors to enter grades;
- forgetting the campus-LAN boundary for catalogue access;
- writing a policy that is syntactically valid but has empty required workflows.

The task is intentionally compact, but it is not a single-rule exercise. A correct solution must compose several interacting authorization dimensions at once: actor role, action kind, resource ownership, registration lifecycle, professor eligibility, schedule conflict, class ownership, grade sensitivity, and liveness of required workflows.

## Review-Bot Risk Mitigations

The automatic review flagged two reasonable risks: possible natural-language ambiguity and possible low difficulty. The task package has been tightened accordingly.

- The requirements now state an explicit least-permissive interpretation and enumerate the main boundaries the policy must preserve.
- The difficulty metadata now emphasizes interacting scoped workflows rather than one compact role policy.
- The hidden tests already check both sides of the target: over-permission through ceilings and under-permission through floors/liveness.

## Anti-Shortcut Design

- The verifier checks semantic containment with Cedar/SymCC, not line-by-line text.
- Broad permit policies fail hidden ceiling checks.
- Under-permissive policies fail floor and liveness checks.
- The task does not depend on AutoCedar or any project-specific agent.
- The oracle solution is provided only for Harbor's oracle agent and reviewer sanity checks.

## Current Local Validation

The oracle solution passes the verifier locally with Cedar CLI 4.10.0 and CVC5 available. A deliberately overbroad `permit (principal, action, resource);` policy fails the hidden ceiling checks, confirming that the grader is not a syntax-only validator.

## Rubric Self-Check

- Verifiable: deterministic `cedar validate` and `cedar symcc` checks.
- Well-specified: requirements, schema, and output path are explicit.
- Solvable: oracle solution exists and passes locally.
- Difficult: requires preserving interacting lifecycle, ownership, role, privacy, and liveness constraints, not just writing syntactically valid Cedar.
- Scientifically grounded: represents a real formal-methods/security-policy engineering workflow.
- Outcome-verified: grading checks the final policy denotation, not the agent trajectory.
