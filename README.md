# CedarForge

`cedarforge/` is a research workspace for building a fine-grained multi-agent system that can use open-source small models to generate Cedar access control policies from a policy description and a schema.

The target is not just to produce policy text, but to produce policies that are:

- syntactically correct
- semantically aligned with the intended access-control requirements
- good enough to approach the behavior of frontier models through system design, verification, and iterative repair

## Why This Exists

Many large enterprises do not want to send internal access-control specifications, schemas, or policy logic to public hosted frontier models.

Because of that, they need a deployable local alternative:

- self-hosted open-source models
- private inference endpoints
- controlled prompting and orchestration
- formal verification loops to compensate for weaker model capability

`cedarforge/` exists to explore how far we can push that setup.

## Core Research Goal

Build a multi-agent Cedar policy generation system in which open-source small models can, from:

- a natural-language policy description
- a Cedar schema

produce an access-control policy that is:

- syntax-correct under Cedar validation
- semantically aligned with the intended policy
- repairable through verifier feedback when the first draft is wrong

## Working Hypothesis

Small open-source models will usually not match frontier models in raw one-shot policy synthesis.

But they may get close if the system around them is strong enough.

That system may include:

- task decomposition across multiple agents
- explicit planning before synthesis
- retrieval of reference patterns
- structured verifier feedback
- counterexample-guided repair
- oscillation detection
- constrained output formats
- iterative search over candidate policies

The main idea is to use system design and formal methods to recover capability that the base small model does not have on its own.

## Relation To The Main Repo

The parent `cedar-synthesis-engine` repo provides the verification backbone:

- `orchestrator.py` for Cedar validation and symbolic verification
- `eval_harness.py` for CEGIS-style evaluation
- `cedar symcc` and `cvc5` for formal checks
- scenario packaging with schema, policy spec, references, and verification plans

`cedarforge/` builds on top of that foundation and focuses on the model/system side:

- open-source small-model evaluation
- local endpoint integration
- multi-agent workflow design
- prompt and feedback strategy design
- benchmark task curation

## What Is Already Built

The repository now contains a first working baseline stack for policy-generation experiments:

- single-model prompt strategy experiments under [src/experiments/single_model_baselines/](src/experiments/single_model_baselines)
- reusable evaluation code under [src/metrics/](src/metrics)
- prepared local datasets with `references/` and `verification_plan.py` so semantic alignment can be checked formally

The current evaluation flow is:

1. `Syntax`
   Use `cedar validate` to determine whether the generated policy is valid Cedar.
2. `Schema`
   Use Cedar validation diagnostics to determine whether the policy grounds correctly to the provided schema.
3. `Semantic`
   Use `verification_plan.py`, `references/*.cedar`, `cedar symcc`, and `cvc5` to test semantic alignment and detect counterexamples.

## Current Layout

- [docs/](docs): research documentation — design decisions, research log, repair loop evolution
- [dataset/](dataset): local task datasets, now including reference policies and verification plans
- [src/test_lm.py](src/test_lm.py): quick local model endpoint test
- [src/experiments/](src/experiments): prompt strategies and single-model baselines
- [src/metrics/](src/metrics): reusable syntax/schema/semantic evaluation code
- [SETUP_COMMANDS.md](SETUP_COMMANDS.md): environment setup and verification commands

## Immediate Directions

- finish benchmarking single-model baselines across prompt strategies
- compare open-source local models with the shared evaluation metrics
- define the multi-agent roles needed for Cedar generation
- test whether multi-agent orchestration beats the strongest single-model baseline
- determine how close verifier-guided small models can get to frontier-model behavior
