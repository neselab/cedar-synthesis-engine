# Terminal-Bench Science Task Proposal

## Proposed Task Title

Cedar Policy Synthesis from Course-Registration Authorization Intent

## Scientific Domain

- Domain: Other Sciences
- Field: Engineering Sciences
- Subfield: Autoformalization / Security Policy Verification

## Short Summary

This task evaluates whether terminal agents can turn realistic natural-language access-control requirements into a deployable Cedar policy store that passes deterministic symbolic verification checks. The agent receives university course-registration authorization requirements and a Cedar schema, then must produce `/app/policy.cedar`. The final artifact is graded by Cedar validation and hidden symbolic floor, ceiling, and liveness checks.

## Task Description

The agent is given a realistic university course-registration access-control scenario. The requirements describe students browsing course offerings, adding/dropping courses only during registration, viewing only their own report cards, professors selecting eligible course offerings only when there is no conflict, professors viewing rosters and entering grades only for classes they teach, and registrar-only student-information and registration-closing actions.

The task provides:

- `/app/requirements.md`: natural-language authorization requirements.
- `/app/schema.cedarschema`: the provided Cedar authorization schema.
- `/app/policy.cedar`: an empty starter policy file.

The agent must synthesize a valid Cedar policy store in `/app/policy.cedar`.

The verifier checks the final policy with `cedar validate` and `cedar symcc`. It verifies hidden ceiling properties for over-permission, floor properties for required access, and liveness checks that ensure required workflows are not empty. The verifier accepts any Cedar policy denotation that satisfies the intended behavior; it does not require matching a particular oracle syntax.

## Why This Is A Good Terminal-Bench Science Task

This is a real engineering-science and formal-methods workflow. Security policy engineers and formal-methods researchers routinely translate organizational authorization requirements into executable policies, validate those policies, and repair them when formal checks expose over-permission or under-permission. The task requires an agent to use the terminal to inspect inputs, write formal policy code, run validators, interpret failures, and repair the artifact.

The task is hard for substantive reasons. A policy can compile and look plausible while still violating the organization's intent. Common mistakes include:

- allowing students to modify another student's schedule;
- allowing registration after the registration window closes;
- allowing students to view another student's report card;
- allowing professors to modify another professor's course offerings;
- allowing non-professors to enter grades;
- forgetting the campus-LAN boundary for catalogue access;
- producing an under-permissive policy that blocks required workflows.

These are semantic composition failures, not formatting errors.

## Verifiability

The task is fully programmatically verifiable. The verifier runs:

1. `cedar validate` to check syntax and type correctness.
2. `cedar symcc implies` for ceiling checks, ensuring the candidate policy is no more permissive than the hidden reference boundaries.
3. `cedar symcc implies` in the opposite direction for floor checks, ensuring required access is included.
4. `cedar symcc always-denies`-based liveness checks, ensuring important request classes are not empty.

The verifier is deterministic and outcome-based. It checks the final policy's behavior, not the agent's process.

## Solvability

An oracle solution exists and passes locally with Cedar CLI 4.10.0 and CVC5 installed. A deliberately overbroad policy such as `permit (principal, action, resource);` fails the hidden ceiling checks, showing that the verifier is not merely checking Cedar syntax.

## Expected Difficulty

An expert familiar with Cedar and formal authorization modeling could solve the task in roughly 1-2 hours. The task is expected to be challenging for frontier terminal agents because it requires preserving several interacting intent boundaries simultaneously:

- lifecycle state,
- ownership/self-access,
- role/action separation,
- professor eligibility,
- schedule-conflict constraints,
- sensitive grade visibility,
- required access/liveness.

## Implementation Status

A draft Harbor/TB-Science task package has been prepared locally under:

`experiments/terminal_bench_science/cedar-policy-synthesis-course-registration`

It includes `instruction.md`, `requirements.md`, `schema.cedarschema`, `policy.cedar`, `solution/solve.sh`, `tests/test.sh`, and a symbolic verifier in `tests/test_policy_semantics.py`.

## Anti-Shortcut Design

- Tests use Cedar/SymCC semantic containment, not line matching.
- Broad permit policies fail ceiling checks.
- Under-permissive policies fail floor or liveness checks.
- The task does not require or expose AutoCedar.
- The oracle solution is only for reviewer/oracle sanity checks.
