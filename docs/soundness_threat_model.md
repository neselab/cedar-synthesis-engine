# Soundness and Threat Model

## What a Verified Policy Guarantees

When the CEGIS loop converges (loss = 0), the candidate policy has been **formally verified** against every check in the verification plan. Concretely:

| Check type | Guarantee |
|---|---|
| `implies` (ceiling) | For all well-typed requests: if the candidate allows it, the ceiling also allows it. The candidate is no more permissive than the ceiling. |
| `floor` | For all well-typed requests: if the floor allows it, the candidate also allows it. The candidate permits at least what the floor requires. |
| `always-denies-liveness` | There exists at least one well-typed request that the candidate allows. The policy is not vacuously restrictive. |
| `never-errors` | For all well-typed requests, the candidate does not produce a runtime error (e.g., accessing a missing attribute). |

These are **universal** guarantees over all possible inputs — not sampled, not bounded, not probabilistic. They hold because the SMT solver exhaustively reasons over the entire input space (see `decidability.md`).

## The Trust Chain

The system's correctness depends on a chain of trust from human intent to verified policy:

```
Human Intent
    ↓ (manual authoring)
NL Policy Spec (policy_spec.md)
    ↓ (LLM generation — Phase 1)
Reference Policies (ceilings + floors)
    ↓ (human review gate)
Approved References
    ↓ (SMT verification — Phase 2)
Verified Candidate Policy
```

Each link in the chain has a different trust basis:

### Link 1: Human Intent → NL Spec

**Trust basis:** Human judgment. The spec is written by a domain expert who understands the organization's access control requirements.

**Failure mode:** The spec is ambiguous, incomplete, or wrong. For example, the spec says "Clinical Researchers can view documents" but doesn't specify that they need clearance > 3.

**Mitigation:** None within the system — this is a problem statement quality issue. The system faithfully implements whatever the spec says, even if the spec is wrong.

### Link 2: NL Spec → Reference Policies

**Trust basis:** LLM generation quality + human review. The LLM translates each NL requirement into a formal Cedar policy (ceiling or floor).

**Failure mode:** The LLM mistranslates a requirement. For example, the spec says "clearance above 3" but the LLM writes `clearanceLevel >= 3` instead of `> 3`.

**Mitigation:** The **human review gate** (Phase 1.5). A human examines each reference policy with its NL summary and either approves or rejects with feedback. This is the critical trust anchor — if a wrong reference policy is approved, the entire verification is sound *with respect to the wrong spec*. The system guarantees `candidate ≤ ceiling`, but if the ceiling itself is wrong, the guarantee is vacuously correct.

**Residual risk:** Human reviewers may miss subtle errors in reference policies, especially in complex conditions with multiple interacting clauses. The NL translation layer (`policy_to_nl`) helps by presenting the policy in plain language, but NL summaries can also be imprecise.

### Link 3: Approved References → Verified Candidate

**Trust basis:** Mathematical proof via SMT solver. Given the approved reference policies, the solver provides a machine-checkable proof that the candidate satisfies all checks.

**Failure mode:** A bug in the SMT solver (CVC5) or the Cedar-to-SMT encoding (`cedar symcc`). These are both large, well-tested codebases, but software bugs are always possible.

**Mitigation:** This is standard trusted computing base (TCB) risk, equivalent to trusting a compiler or an OS kernel. CVC5 is a mature solver with extensive testing and competition verification. Cedar's `symcc` is maintained by the Cedar team at AWS.

## What the System Does NOT Guarantee

### Completeness of the specification

The system verifies that the candidate conforms to the reference policies. It does **not** verify that the reference policies capture all intended requirements. If a requirement is missing from the verification plan (e.g., no floor check for a certain access path), the candidate may violate that requirement without detection.

**Example:** The GitHub scenario has floor checks for `writer_edit` and `reporter_delete`, but if we omitted the `reporter_delete` floor, the candidate could exclude the reporter self-delete path and still pass all remaining checks.

### Behavioral equivalence to existing policies

The system does not check that the synthesized policy is equivalent to any existing policy in `policy_store.cedar`. The candidate is verified against the reference policies, not against prior policies. If the organization's existing policies have different semantics than the reference policies, the candidate may behave differently.

### Temporal properties

Cedar policies are stateless — they evaluate a single request at a time. The system cannot verify temporal properties like "a user who was denied 3 times should be locked out" or "access should expire after 30 days." These require runtime enforcement mechanisms outside Cedar's scope.

### Side-channel properties

The system verifies logical correctness (what is allowed/denied) but not performance properties (e.g., "evaluation should take < 10ms") or information-flow properties (e.g., "the denial message should not reveal which condition failed").

## Threat Model

### Trusted components

| Component | Trust assumption |
|---|---|
| Cedar CLI (`cedar validate`, `cedar symcc`) | Correctly implements Cedar semantics and SMT encoding |
| CVC5 solver | Sound and complete for the theories used |
| Schema (`*.cedarschema`) | Correctly models the entity types and relationships |
| Human reviewer | Reviews reference policies carefully and catches errors |

### Untrusted components

| Component | Why untrusted | How the system handles it |
|---|---|---|
| LLM (Phase 1: reference generation) | May mistranslate NL to Cedar | Human review gate catches errors |
| LLM (Phase 2: candidate synthesis) | May produce incorrect candidates | SMT verification catches every error |
| NL Policy Spec | May be ambiguous or incomplete | Out of scope — garbage in, garbage out |
| NL Translation (`policy_to_nl`) | May produce imprecise summaries | Used only for human review aid, not for verification |

The key insight: the LLM is **never trusted for correctness**. It is used as a heuristic generator — a source of plausible candidates that the formal verifier either accepts or rejects. The LLM's role is to reduce the search space, not to provide guarantees.

### Attack surfaces

If an adversary controls any trusted component:

| Compromised component | Impact |
|---|---|
| Schema | Adversary can make the type system admit requests the organization doesn't intend. Verification is sound w.r.t. the wrong schema. |
| Reference policies (post-review) | Adversary can set a permissive ceiling or restrictive floor. Verification ensures the candidate matches the adversary's spec. |
| Cedar CLI / CVC5 | Adversary can forge proofs. Candidate appears verified but may be incorrect. |

In all cases, the system's guarantees are relative to the trusted components. The system does not defend against supply chain attacks on the solver or CLI tooling.

## The Role of the Human Review Gate

The human review gate is not a formality — it is the **critical trust boundary** in the system. Everything upstream of the gate (LLM generation) is untrusted. Everything downstream (SMT verification) is mechanically trustworthy.

The gate works because:

1. **Reference policies are simple.** Each encodes a single property about a single action — a 1:1 translation from one NL requirement. Reviewing a 5-10 line Cedar policy is tractable for a security engineer.

2. **NL summaries aid comprehension.** The `policy_to_nl` translation presents each policy in business language, reducing the Cedar expertise required.

3. **Feedback enables iteration.** If the reviewer spots an error, they can describe the issue in natural language, and the LLM regenerates the reference policy. The reviewer does not need to write Cedar.

4. **The review scope is bounded.** A typical scenario has 5-10 reference policies. This is a finite, manageable review task — unlike reviewing a full candidate policy with interacting rules.

The `--no-review` flag bypasses this gate for automated benchmarking. Results from `--no-review` runs should be interpreted as measuring the LLM's synthesis capability, not the system's end-to-end correctness guarantee.
