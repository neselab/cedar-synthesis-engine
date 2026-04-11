# CedarForge System Design

This document captures the intended system design for CedarForge.

## Core Question

Under what conditions can open-source small models approach frontier-model performance on Cedar policy generation?

The target task is:

- input:
  natural-language policy description plus Cedar schema
- output:
  Cedar policy that is syntax-correct and semantically aligned

Verification is done with the existing Cedar validation and SMT-based symbolic checks.

## Development Order

The system should be built in two stages.

### Stage 1: Single-Model Baseline

First, establish the capability boundary of a single model.

The baseline prompt variants are:

- zero-shot direct
- structured instruction
- chain-of-thought style prompting
- grounded few-shot prompting
- contrastive few-shot prompting

This stage answers:

- what the model can already do
- where syntax breaks
- where semantic alignment breaks
- which prompting methods help most

### Stage 2: Multi-Agent System

Only after the single-model baseline is solid should we introduce multiple agents.

This prevents confusion between:

- gains from better prompting
- gains from better orchestration

## Multi-Agent Principles

### 1. Split planning and grounding

The pipeline should not treat policy generation as one monolithic step.

Instead:

- a planning module produces high-level subgoals
- grounding agents implement those subgoals in Cedar

### 2. No unrestricted free discussion

Agents should not chat arbitrarily.

Instead, communication should be:

- structured
- role-bounded
- checkable

This makes debugging and alignment easier.

### 3. Small agent squad with explicit roles

The initial target is a 3-agent or 4-agent squad.

Possible roles:

- Planner:
  extracts subgoals from the policy description
- Grounder:
  maps subgoals into Cedar policy fragments
- Critic / Alignment Checker:
  checks whether the grounded policy still matches the subgoals
- Repair Agent:
  uses verifier feedback to revise the candidate

### 4. External knowledge should be injected explicitly

Agents should not be forced to rely only on parametric memory.

They should receive:

- Cedar syntax cheat sheet
- policy skeletons
- grounded examples
- contrastive examples

This reduces hallucination and raises reliability.

### 5. Structured outputs

Agent communication should use constrained schemas rather than free-form prose whenever possible.

Examples:

- JSON subgoal lists
- structured role-to-action mappings
- explicit permit and forbid candidate fragments
- checklists for unresolved policy requirements

### 6. Structured retrieval

Relevant syntax patterns, examples, and task-specific references should be retrieved deliberately rather than dumped into the prompt.

The retrieval layer should help the agent answer:

- what Cedar construct is relevant here
- which policy pattern matches this kind of rule
- what common failure mode should be avoided

## Evaluation

Two evaluation dimensions matter.

### Syntax correctness

Use Cedar validation against the schema.

### Semantic alignment

Use ceiling/floor/liveness checks through SMT-backed symbolic verification.

A model should not be treated as successful if it merely produces well-formed Cedar.

## Research Hypothesis

Open-source small models may not match frontier models in raw one-shot generation.

But they may get much closer if the surrounding system provides:

- decomposition
- retrieval
- external syntax support
- structured coordination
- verifier-guided correction

That is the main thesis behind CedarForge.

