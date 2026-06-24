# External Dataset Reuse Plan

This note records how AutoCedar can use two external source families in a
paper or experiment without overstating what they provide:

1. REDE `data/AccessControlModelStudy` for natural-language access-control
   intent extraction and schema/policy atomization.
2. Official `cedar-policy` repositories for Cedar language provenance,
   verifier alignment, and regression material.

## Source Inventory

### REDE AccessControlModelStudy

The REDE repository is Apache-2.0 licensed. Its `AccessControlModelStudy`
directory contains raw requirements sources and labeled exports:

- `CyberChair/`
- `Xiao Sources/`
- `iTrust/`
- `ibm use case/`
- `labelled data sets/`

The labeled exports include five spreadsheet/text pairs:

- `Collected ACP Sentences`
- `CyberChair`
- `IBM Course Management`
- `iTrust for ACRE`
- `iTrust for Text2Policy`

The text exports use sentence lines followed by extracted triples:

```text
2.0:An HCP creates patients.
          hcp;create;patient - C
```

Some triples include negation markers:

```text
          hcp;edit;password;NEG-not - U
```

The CRUD codes are weak action hints, not Cedar actions by themselves:

- `C`: create-like action
- `R`: read/view/access-like action
- `U`: update/edit-like action
- `D`: delete/remove-like action
- `E`: execute/session/action event

Running `scripts/rede_intent_atoms.py` over the labeled text exports produced
this inventory:

| Subset | Sentence lines | AC sentence lines | Triples | Empty-subject triples | Negated triples |
| --- | ---: | ---: | ---: | ---: | ---: |
| `Collected ACP Sentences` | 142 | 112 | 258 | 5 | 39 |
| `CyberChair` | 303 | 139 | 386 | 187 | 0 |
| `IBM Course Management` | 401 | 169 | 379 | 35 | 4 |
| `iTrust for ACRE` | 1160 | 549 | 2270 | 553 | 24 |
| `iTrust for Text2Policy` | 471 | 418 | 1070 | 222 | 19 |
| **Total** | **2477** | **1387** | **4363** | **1002** | **86** |

### Official Cedar Repositories

The `cedar-policy` GitHub organization currently includes the primary Cedar
implementation, examples, formal specification, docs, integrations, and
language bindings. The most relevant repositories for AutoCedar are:

- `cedar-policy/cedar`: Rust implementation, CLI, validator, and SymCC.
- `cedar-policy/cedar-examples`: policies, schemas, entities, sample apps,
  and OOPSLA 2024 benchmark code.
- `cedar-policy/cedar-spec`: Lean formalization, DRT, fuzzing, and policy
  generators.

The official examples overlap with AutoCedar's mutation-scenario roots:
`document_cloud`, `github_example`, `hotel_chains`, `sales_orgs`,
`streaming_service`, `tags_n_roles`, `tax_preparer`, and `tinytodo`.
AutoCedar extends that seed material into 79 mutation scenarios and 142
hand-authored realworld scenarios.

## What REDE Is Good For

REDE is useful as an intent formalization dataset, not as a direct Cedar
policy-synthesis ground truth.

It can support these tangible experiments:

1. **Access-control sentence detection.** Measure whether AutoCedar identifies
   which requirement sentences contain access-control intent.
2. **Weak intent atom extraction.** Compare model-proposed subject/action/
   resource atoms against REDE triples with normalization.
3. **Negation detection.** Check whether the agent preserves `NEG-not` style
   prohibitions as deny/ceiling candidates instead of permits.
4. **CRUD/action mapping.** Measure whether extracted verbs and CRUD labels
   map to coherent Cedar action atoms after HITL review.
5. **Schema atom proposal quality.** Evaluate proposed entity/action/attribute
   atoms against the REDE triples and the surrounding requirements document.
6. **Human review burden.** Record approve/edit/reject/question rates for
   schema and property atoms on REDE-backed tasks.
7. **Formalization yield.** Track how many weak intent atoms can be converted
   into typechecking Cedar schema plus verifiable property atoms after human
   review.

Recommended first subsets:

| Subset | Use |
| --- | --- |
| `Collected ACP Sentences` | Diverse, compact extraction benchmark. |
| `IBM Course Management` | Coherent domain for first end-to-end formalization. |
| `iTrust for Text2Policy` | Healthcare-style requirements with many labels. |
| `CyberChair` | Noisy extraction stress test, not the primary headline. |

## What REDE Is Not Good For

Do not claim REDE is a ready Cedar benchmark. The labels are noisy extraction
triples, not formal policies:

- Many triples have empty subjects.
- Resources and actions are often vague noun/verb phrases.
- Entity hierarchies, context attributes, temporal conditions, and exceptions
  are mostly absent or implicit.
- CRUD labels are coarse hints and sometimes multi-letter composites.
- There are no Cedar schemas, no reference policies, and no SymCC check plans.

Any Cedar scenario derived from REDE needs a human-reviewed formalization step.
That fits AutoCedar's thesis, but it must be presented as HITL conversion, not
automatic ground-truth evaluation.

## Repeatable Import Path

Clone REDE outside this repository:

```bash
git clone https://github.com/RealsearchGroup/REDE.git /tmp/REDE
```

Convert the labeled text exports to weak intent atoms:

```bash
python scripts/rede_intent_atoms.py \
  /tmp/REDE/data/AccessControlModelStudy \
  --out /tmp/rede_intent_atoms.jsonl \
  --summary /tmp/rede_intent_summary.json
```

The JSONL records have this shape:

```json
{
  "dataset": "iTrust for Text2Policy",
  "sentence_id": "8.0",
  "sentence": "The HCP does not have the ability to enter the patient's security question and password.",
  "subject_text": "hcp",
  "action_text": "enter",
  "resource_text": "password",
  "negated": true,
  "crud": "C",
  "crud_ops": ["C"]
}
```

These are **weak intent atoms**. They should seed AutoCedar's chat/context and
HITL atomization flow, not bypass it.

## Proposed Paper Experiment

### Experiment A: REDE Intent Atomization

Input: REDE sentence text and, optionally, the surrounding source document.

Agent task: propose schema atoms and policy-intent atoms. The chat model may
use the REDE labels only for evaluation, not as hidden prompt context.

Human task: approve, reject, edit, or question proposed atoms using the normal
AutoCedar HITL loop.

Metrics:

- Access-control sentence precision/recall.
- Subject/action/resource exact and normalized F1.
- Negation precision/recall.
- CRUD-to-Cedar-action mapping agreement.
- Atom review burden: approve/edit/reject/question counts.
- Formalization yield: fraction of weak atoms surviving into validated schema
  and property atoms.
- Validation yield: fraction of curated tasks producing `cedar validate`
  passing schemas and SymCC-checkable reference policies.

### Experiment B: REDE-to-Cedar Curated Scenarios

Take 5-10 coherent slices from `IBM Course Management` and `iTrust for
Text2Policy`. Use AutoCedar to propose schema/property atoms, then have a
human approve the final formalization and write reference bounds.

Report:

- Human time and review actions.
- Final schema and verification-plan size.
- Whether Stage 3 synthesis converges.
- Which intent ambiguities required human judgment.

This gives a tangible end-to-end demonstration while preserving the trust
anchor: Cedar correctness comes from human-reviewed formal bounds and SymCC,
not from the REDE triples alone.

### Experiment C: Official Cedar Regression Alignment

Use `cedar-policy/cedar-examples` and `cedar-policy/cedar` sample data to show
that AutoCedar's generated artifacts remain aligned with official Cedar
constructs.

Report:

- Which official example domains seeded the mutation benchmark.
- Validation of generated schemas/policies with the official Cedar CLI.
- Mapping from AutoCedar check types to SymCC properties:
  - `ceiling` -> `implies(candidate, reference)`
  - `floor` -> `implies(reference, candidate)`
  - `liveness` -> inverted `always_denies`
  - future: `equivalent` and `disjointness`

Use `cedar-policy/cedar-spec` for theory framing: Cedar's formalization and
DRT infrastructure support the claim that AutoCedar is building on a language
designed for automated reasoning.

## Bottom Line

Use REDE for the natural-language intent side of the paper. Use official Cedar
repositories for formal-language alignment and regression provenance. Do not
merge those claims: REDE does not validate Cedar policy correctness, and Cedar
examples do not test real prose intent extraction. Together, they make the
AutoCedar story stronger because they cover the two halves of the pipeline.
