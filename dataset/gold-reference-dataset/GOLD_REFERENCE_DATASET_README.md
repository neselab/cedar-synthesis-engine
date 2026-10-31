# Gold-reference authorization dataset

This package contains 200 synthetic authorization cases spanning 43 application domains. Each case pairs a natural-language requirement with a gold Cedar policy and schema. The saved structured inputs and compiler reproduce the gold outputs without an LLM call.

## Package contents

| Path | Contents |
| --- | --- |
| [cases/](cases/) | All 200 cases, each with the same seven files described below. |
| [construction/skeletons.json](construction/skeletons.json) | Source domain skeletons, actions, and available authorization rules. |
| [construction/rewrite-prompt.md](construction/rewrite-prompt.md) | Prompt used to turn controlled English into an organizational requirement. |
| [compiler.py](compiler.py) | Deterministic translator from a complete specification and registry to Cedar. |
| [verify_gold.py](verify_gold.py) | Recompile the saved cases and compare their gold outputs. |

## How the dataset was constructed

### 1. Define domain skeletons and actions

We began with manually designed domain skeletons. LLM assistance expanded candidate actions and authorization rules, and the source definitions were manually reviewed before case construction. A skeleton describes an application's roles, resources, attributes, request context, actions, and related action chains. An **anchor** is an action with a defined menu of authorization rules from which a case can be built. The 200 cases in this package cover 43 domains.

### 2. Define exact rules and parameter choices

For each domain, a **typed registry** defines the Cedar entity and field types, optional attributes, role and state values, action eligibility, mandatory action prerequisites (domain gates), predicates, and allowed parameter choices. Each case saves the registry used to compile its gold artifacts.

The library uses five rule families: separation of duty (G1), binding of duty (G2), scoped overrides (G3), authority dominance (G4), and state prerequisites (G5). G1, G2, G4, and G5 supply **base rules**; G3 supplies overrides of named bases.

There are also 14 condition families: identity, role, group or hierarchy membership, set membership, strings, integer comparisons, arithmetic, monetary thresholds, network, time, state, optional-field presence or Boolean flags, tags, and request-context facts. The domain and anchor determine each condition's exact fields and predicate.

Each condition has a predefined form and target:

| Form | Meaning |
| --- | --- |
| `require` | Must hold unless a named exception waives it. |
| `prohibit` | The blocking condition must be false. |
| `applicability` | Activates its named base when true. |
| `obligation` | Requires the specified consequence when its trigger holds. |
| `exception` | Waives only its named base or mandatory requirement. |

Concrete values, such as monetary thresholds, are authored choices for these synthetic organizational policies. Authorization follows the explicit predicates and domain gates in the saved registry; descriptive notes and numeric metadata do not add access restrictions.

### 3. Sample rules and complete the specification

The sampler selects a domain, an anchor or a declared chain of anchors, and compatible bases, conditions, and overrides. At most five elements are selected per anchor, counting those three categories together. Conditions retain their predefined forms and targets, and references to unselected rules are rejected.

A parameter-completion program selects concrete values from the registry's allowed choices using the sampled structure and a recorded seed. This yields a **complete specification**: selected actions, rule IDs, forms, targets, parameters, and overrides are all explicit. The saved specifications already contain these values.

### 4. Compile the gold policy and schema

The compiler reads only `spec.json` and `registry.json`. It checks selections and operand types, substitutes concrete parameters, protects optional-field reads with presence checks, and composes the authorization conditions. Each selected action receives one typed Cedar `permit`; unselected actions receive no permit. For each selected action, the compiler requires its domain gate, an eligibility route, every normalized base, and every action requirement. Eligibility is satisfied by the ordinary route or an additional route explicitly supplied by a selected override.

For a base B, let A be the OR of its applicability triggers, or true if none are selected. Let W be the OR of its named waivers, or false if none are selected. The base contributes `NOT A OR B OR W`. A waiver affects only its declared target. A conditional obligation is already defined by a complete trigger-and-consequence expression in the registry.

The schema comes from the same registry and selected actions. It retains the registry's entity and context declarations, including unused fields. Declaring a field does not impose an authorization rule. Action chains describe related requests against recorded facts; they do not execute state transitions.

The compiler also produces a predicate abstract syntax tree (AST), exposing the composed authorization expression. The same saved specification, registry, and compiler produce the same policy, schema, and AST.

### 5. Write the natural-language requirement

A deterministic renderer first expressed the complete rules as controlled English. An LLM then used the saved rewrite prompt to express those rules as an organizational requirement, preserving thresholds, boundaries, mandatory facts, conditional duties, and exception scopes. A separate automated model review checked the rewrite against its controlled source for omitted, added, or changed rules. This text check was separate from the earlier manual review of the source definitions.

The English rewrite does not change the gold outputs. This package reproduces gold compilation from the saved complete inputs; sampling and language rewriting are described as construction steps.

## The seven files in each case

| File | Purpose |
| --- | --- |
| `requirement.md` | Final natural-language organizational requirement. |
| `controlled-source.txt` | Explicit English intermediate used to prepare and check the rewrite. |
| `gold/spec.json` | Complete selected actions, rules, forms, targets, and parameter values. |
| `gold/registry.json` | Exact typed definitions, predicates, parameter catalogs, and composition targets. |
| `gold/gold.cedar` | Compiled gold policy. |
| `gold/schema.cedarschema` | Compiled Cedar schema. |
| `gold/predicate_ast.json` | Instantiated authorization expression produced by the compiler. |

Case identifiers retain their saved names. There are 200 case directories; the numerical identifiers are not consecutive.

## Example: case-100

[case-100](cases/case-100/requirement.md) concerns reimbursement disbursement. Its [specification](cases/case-100/gold/spec.json) selects separation of duty (G1), mandatory approver presence (V12), and a monetary condition (V8) that activates G1 above 25,000 cents. The [registry](cases/case-100/gold/registry.json) defines the types, Controller eligibility, a nonnegative-amount gate, and the exact predicates.

The resulting [gold policy](cases/case-100/gold/gold.cedar) permits disbursement exactly when:

```text
requester has Controller role
AND reimbursement amount >= 0
AND the report has a recorded approver
AND (amount <= 25000 OR requester differs from approver)
```

Thus a Controller recorded as the approver can disburse $250, but cannot disburse $250.01. A different approver satisfies the separation of duty rule above that threshold. A recorded approver is required at every amount. The [schema](cases/case-100/gold/schema.cedarschema) supplies the types, while the [controlled source](cases/case-100/controlled-source.txt) and [natural-language requirement](cases/case-100/requirement.md) provide the two English presentations.

## Reproduce the gold outputs

With Python 3.9 or later, run from this package directory:

```bash
python3 verify_gold.py
```

This checks that there are 200 cases with the seven expected files, recompiles every complete specification, and compares the policy and schema text and parsed predicate AST with the saved outputs. It requires no external Python packages, model access, or Cedar executable.

To inspect one case:

```bash
python3 verify_gold.py --case case-100
```

These commands reproduce the saved compiler outputs. They do not rerun sampling, LLM rewriting, or Cedar's own validation and symbolic checks.
