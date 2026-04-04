# Decidability of Cedar CEGIS

## Why Decidability Matters

Counterexample-Guided Inductive Synthesis (CEGIS) requires a **verifier** that can, for any candidate program, either confirm correctness or produce a counterexample. In general program synthesis this verification step is undecidable — there is no algorithm guaranteed to terminate for arbitrary programs. This forces practical CEGIS implementations to use bounded model checking, fuzzing, or other incomplete methods that may miss bugs or fail to terminate.

Cedar policy verification is **decidable**. The verifier always terminates with a definitive yes/no answer, and when the answer is no, it produces a concrete counterexample. This gives us a CEGIS instance with a **sound and complete oracle** — a rare property that eliminates an entire class of failure modes.

## The Cedar Decidable Fragment

Cedar's policy language is intentionally restricted to ensure decidable analysis. The key design constraints:

### No recursion or loops

Cedar policies are flat permit/forbid rules with `when`/`unless` guard conditions. There are no user-defined functions, no recursion, and no iteration. Every policy evaluation terminates in bounded time.

### Finite entity hierarchy traversal

The `in` operator checks entity group membership (e.g., `principal in resource.readers`), which requires traversing the entity hierarchy. Cedar bounds this: the hierarchy is a DAG with finite depth, and `in` is evaluated as reachability — a decidable graph property.

### Restricted attribute types

Cedar attributes are restricted to booleans, longs, strings, sets, records, and extension types (IP addresses, decimals, datetimes). There are no floating point numbers, no arbitrary-precision integers, and no user-defined types with custom equality. Every type has a decidable theory in SMT.

### No quantifiers in policy conditions

Policy `when` clauses are quantifier-free boolean combinations of attribute comparisons, set membership tests, and function applications. There are no existential or universal quantifiers over entities. This keeps conditions in the quantifier-free fragment of the combined SMT theories.

### String domains via `@domain` annotations

Unbounded string comparisons (`principal.department == resource.managingDepartment`) are technically in a decidable theory (the theory of strings), but can be expensive. Cedar's `@domain` annotation constrains string attributes to a finite set of values, reducing string reasoning to finite enumeration — a cheaper decidable fragment.

## The SMT Encoding

`cedar symcc` compiles Cedar policies into SMT-LIB formulas and dispatches them to CVC5. The encoding maps:

| Cedar construct | SMT theory |
|---|---|
| Boolean conditions (`&&`, `\|\|`, `!`) | Propositional logic |
| Long comparisons (`>`, `<`, `==`) | Linear integer arithmetic (LIA) |
| String equality/inequality | Theory of strings (or finite enumeration with `@domain`) |
| Set membership (`in`, `contains`) | Theory of sets / finite model |
| Entity hierarchy (`principal in Group`) | Uninterpreted functions + reachability axioms |
| Extension types (IP, datetime) | Bit-vector / integer encodings |

CVC5 supports the combined theory (via Nelson-Oppen combination) and has a decision procedure for each fragment. Since Cedar restricts policies to the quantifier-free combined theory, CVC5 is guaranteed to terminate.

## The Three Decidable Queries

Each verification check in the CEGIS loop maps to a decidable SMT query:

### 1. Implies (subsumption)

```
cedar symcc implies --policies1 <candidate> --policies2 <ceiling>
```

Query: Is there a well-typed request where `candidate` allows but `ceiling` denies?

```
∃ request : candidate.allows(request) ∧ ¬ceiling.allows(request)
```

- **SAT** → counterexample found (candidate is too permissive) → FAIL
- **UNSAT** → no such request exists → PASS (candidate ≤ ceiling)

### 2. Always-denies (liveness, inverted)

```
cedar symcc always-denies --policies <candidate>
```

Query: Does the candidate deny every well-typed request for this action?

```
∀ request : candidate.denies(request)
```

Equivalently: is `∃ request : candidate.allows(request)` UNSAT?

- **VERIFIED** (always denies) → the policy is vacuous → inverted to FAIL for liveness
- **NOT VERIFIED** → some request is allowed → inverted to PASS

### 3. Never-errors (runtime safety)

```
cedar symcc never-errors --policies <candidate>
```

Query: Is there a well-typed request that causes a runtime error (e.g., accessing a missing attribute)?

```
∃ request : candidate.errors(request)
```

- **UNSAT** → no errors possible → PASS
- **SAT** → counterexample triggers an error → FAIL

All three queries are existential (or universals reduced to negated existentials), quantifier-free, and over decidable theories. CVC5 is guaranteed to return SAT or UNSAT in finite time.

## Termination vs. Convergence

Decidability guarantees that each **verification step** terminates. It does not guarantee that the **CEGIS loop** converges — the LLM might produce infinitely many incorrect candidates. In practice, we bound the loop with a maximum iteration count (default: 20).

However, decidability provides a stronger property than bounded model checking: every counterexample is a **true** counterexample (no false positives from incomplete analysis), and every PASS is a **true** proof (no false negatives). This means:

1. The LLM never wastes iterations chasing phantom bugs
2. A converged policy is provably correct (not just "we didn't find a bug")
3. The feedback signal is always actionable — each counterexample points to a real violation

## Practical Bounds

While verification is decidable in theory, practical runtime depends on:

| Factor | Impact | Mitigation |
|---|---|---|
| Number of entity types | More types = larger SMT formula | Cedar schemas are typically small (5-20 types) |
| Attribute domain size | `@domain` with many values = more cases | Keep domains small; solver handles ~100 values easily |
| Policy rule count | Each rule adds conjuncts/disjuncts | Candidate policies are typically 3-15 rules |
| Hierarchy depth | Deep `in` chains = more reachability axioms | Cedar hierarchies are typically 2-4 levels |

In our experiments, all verification queries complete in under 1 second. The 30-second timeout in `solver_wrapper.py` has never been hit.

## Comparison to Undecidable Settings

| Property | Decidable CEGIS (Cedar) | Undecidable CEGIS (general) |
|---|---|---|
| Verifier termination | Guaranteed | Not guaranteed |
| Counterexample validity | Always true (sound) | May be spurious |
| Proof validity | Always true (complete) | May miss bugs |
| Convergence guarantee | No (LLM-dependent) | No |
| Iteration quality | Every iteration is informative | Some iterations wasted on false alarms |

The decidability of Cedar verification is what makes the CEGIS loop practical with LLMs. LLMs are imprecise generators — they need a precise oracle to compensate. An unsound verifier would compound the LLM's imprecision; a sound and complete one corrects it.
