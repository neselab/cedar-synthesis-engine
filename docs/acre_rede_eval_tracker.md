# ACRE/REDE Case Study Evaluation Tracker

This is the maintained table for Part 1 of the external-corpus evaluation:
turning ACRE/REDE natural-language access-control material into reviewed,
verifier-backed Cedar artifacts with AutoCedar.

## Evaluation Takeaway

The external-corpus story is not "AutoCedar translated one paragraph into one
policy." The stronger result is that AutoCedar takes messy upstream access
control material -- prose requirements plus NLACP-style relation labels -- and
compresses it into a small set of deployable, human-reviewed Cedar artifacts:

1. a Cedar schema whose entities, actions, relationships, and context hooks were
   reviewed as intent atoms;
2. a verifier signal layer whose floor, ceiling, liveness, and disjointness
   properties were reviewed independently from the final policy text;
3. a final Cedar policy store that converges against those independently
   reviewed checks.

That is the benefit to show in the paper: the system turns hundreds or
thousands of noisy natural-language and NLACP facts into one coherent Cedar
domain model plus one coherent policy store, while preserving a reviewable path
from source prose to formal intent to machine-checked policy behavior.

## Before/After Summary

This is the paper-facing view. It compresses each case study into the shape a
reviewer needs first: input scale, reviewed formal output, repair burden, and
synthesis cost. Full provenance and per-run details remain below.

| Dataset/slice | Input scale | Reviewed output | Repair burden | Synthesis outcome | Time/cost |
| --- | --- | --- | --- | --- | --- |
| IBM Course Management | 401 sentences / 379 local triples | 44 schema atoms; 19-21 checks | 3 lifecycle hooks in repaired rerun | loss 0 in 2/20 iters | 73.46s / $0.0834 |
| CyberChair | 303 sentences / 386 local triples | 55 schema atoms; 42 checks | 1 reviewer-page auth hook | loss 0 in 1/20 iter | 64.43s / $0.0663 |
| iTrust for Text2Policy | 471 sentences / 1070 local triples | 73 schema atoms; 53 checks | 3 healthcare/domain hooks | loss 0 in 2/20 iters | 213.33s / $0.2222 |
| iTrust for ACRE | 1160 sentences / 2270 local triples | 97 schema atoms + 1 typed-session repair; 82 checks | typed session ownership repair | loss 0 in 2/20 iters | 303.81s / $0.3047 |
| Collected ACP gradebook slice | 142 sentences / 258 local triples | 15 schema atoms; 15 checks | 1 final-responsibility hook | loss 0 in 2/20 iters | 266.35s / $0.2394 |

Read this as a compression result: the largest slice starts with 1160
sentences and 2270 extracted relation triples, then lands as a reviewed Cedar
schema plus 82 independently checked formal signals and a converged policy
store. The output is smaller, executable, and verifier-backed.

## What The Approach Buys Us

| Problem in the source material | What AutoCedar adds | Why it matters |
| --- | --- | --- |
| NLACP labels are many small relation fragments, not a deployable authorization system. | A unified Cedar schema and policy store for each coherent scenario slice. | The output is deployable policy infrastructure, not another weak-label extraction artifact. |
| Requirements mix permissions, prohibitions, lifecycle facts, entity relationships, and system behavior. | Intent atomization separates schema facts from policy/property facts, then reviews them independently. | A human can approve or repair the exact formal intent before the final policy is synthesized. |
| Independent NLACP policies can overlap or scope-creep when naively translated one by one. | Floor/ceiling/liveness/disjointness checks constrain the final policy store compositionally. | The final policy is checked against the whole reviewed intent layer, not only against isolated clauses. |
| Real requirements often reveal missing schema concepts late. | Schema repair turns policy-intent failures into explicit schema hooks before synthesis. | The system does not silently approximate missing concepts with broader, less safe policies. |
| A direct NL-to-Cedar prompt gives one opaque output. | AutoCedar produces inspectable artifacts: schema, property plan, references, candidate policy, logs. | Reviewers can audit where each formal concept came from and where the verifier accepted it. |

## Cost And Time Summary

| Dataset/slice | Completed mode | Final checks | Iterations | Total tokens | Est. API cost | Stage 3 time |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| IBM Course Management, prior full HITL | HITL | 21 | 1/20 | 7326 | $0.0660 | 68.32s |
| IBM Course Management, semantic-boundary rerun | HITL with supplied reviewed schema and schema repair | 19 | 2/20 | 12131 | $0.0834 | 73.46s |
| CyberChair | HITL | 42 | 1/20 | 8201 | $0.0663 | 64.43s |
| iTrust for Text2Policy | HITL with reviewed schema from r2 | 53 | 2/20 | 27784 | $0.2222 | 213.33s |
| iTrust for ACRE | HITL curated | 82 | 2/20 | 35311 | $0.3047 | 303.81s |
| Collected ACP gradebook slice | HITL | 15 | 2/20 | 26062 | $0.2394 | 266.35s |

Interpretation: the larger healthcare runs cost cents, not dollars, for the
model-backed synthesis loop once the reviewed intent artifacts exist. The
missing number is human semantic-review time; future runs should record it
separately because it is the main operational cost of HITL formalization.

## Source Background

The relevant lineage is John Slankas's ACRE work:

- Slankas and Williams, **"Access Control Policy Extraction from
  Unconstrained Natural Language Text"** (PASSAT/SocialCom 2013), introduces
  Access Control Relation Extraction (ACRE): extracting subject/action/resource
  access-control tuples from existing unconstrained natural-language artifacts.
- Slankas, Xiao, Williams, and Xie, **"Relation Extraction for Inferring
  Access Control Rules from Natural Language Artifacts"** (ACSAC 2014), extends
  the relation-extraction evaluation over healthcare, education, and conference
  management systems.

The ACRE/REDE material is useful to AutoCedar because it gives realistic
upstream artifacts: prose requirements and NLACP-style relation labels. It does
not give Cedar schemas, Cedar policies, or symbolic verification plans. The
AutoCedar contribution is the formalization layer: HITL-reviewed schema atoms,
HITL-reviewed property/signal atoms, generated Cedar references, and a final
Cedar policy store checked against those signals.

Primary source links:

- PASSAT/SocialCom 2013 paper PDF:
  <https://www.slankas.net/papers/passat2013_slankas.pdf>
- ACSAC 2014 program page:
  <https://www.acsac.org/2014/program-final/s183.html>
- ACSAC 2014 slide deck:
  <https://www.acsac.org/2014/program-final/oc_multifile/3/183.pdf>
- ACSAC 2014 DOI:
  <https://doi.org/10.1145/2664243.2664280>

## Corpus Inventory

The ACSAC 2014 slide deck reports these corpus-level counts. The local REDE
text exports are parsed by `scripts/rede_intent_atoms.py`; local counts can
vary slightly from the paper table because the current text exports and parser
normalization are not exactly the paper's annotation pipeline.

| Corpus subset | Domain | Sentences, paper | ACR sentences, paper | ACRs, paper | Local parsed triples | Empty-subject triples, local | Negated triples, local |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| IBM Course Management | Education | 401 | 169 | 375 | 379 | 35 | 4 |
| CyberChair | Conference management | 303 | 139 | 386 | 386 | 187 | 0 |
| iTrust for ACRE | Healthcare | 1160 | 550 | 2274 | 2270 | 553 | 24 |
| iTrust for Text2Policy | Healthcare | 471 | 418 | 1070 | 1070 | 222 | 19 |
| Collected ACP Documents | Mixed | 142 | 114 | 258 | 258 | 5 | 39 |

## Measurement Schema

For every reported run or slice, keep these fields:

| Field | Meaning |
| --- | --- |
| Dataset and slice | Dataset name, scenario subset, and whether the run used full prose, selected NLACP labels, or both. |
| Source files used | Exact REDE relative paths used as input/provenance. |
| Input scope | Sentence ID range and selected NLACP policy sentences/triples, when available. |
| Schema path | Whether the run supplied a schema or had AutoCedar propose schema atoms from NL. |
| Schema review | Schema atoms proposed, approved, edited, rejected, questioned. |
| Property review | Property atoms proposed, approved, edited/repaired, rejected, questioned. |
| Schema gaps/repairs | Schema gaps discovered during property review and whether repairs were applied. |
| Reference checks | Number of final verifier checks and generated reference policies. |
| Stage 3 synthesis | Model, convergence, iterations, final loss, and notable failure modes. |
| Synthesis time | Stage 3 harness/model time from `eval_log.json`; do not treat this as total human-review wall-clock time. |
| Token and dollar cost | Total input/output tokens and estimated model cost from run logs. |
| Artifacts | Final schema, verification plan, references, policy store, final candidate, logs. |
| Human effort | Manual semantic-review time and notable ambiguity classes. This is not captured yet. |

## Part 1 Run Matrix

Part 1 asks whether AutoCedar can take ACRE/REDE-style natural-language
requirements plus NLACP provenance labels and produce Cedar-ready artifacts:
schema, reviewed property signals, final references, and a synthesized policy
store. Rows marked HITL use manually reviewed atom semantics. Rows marked AITL
are automated-agent baselines and must not be described as human semantic
review.

| Dataset | Slice | Reviewer mode | Status | What exists now | Main paper use |
| --- | --- | --- | --- | --- | --- |
| IBM Course Management | Course registration/report-card/professor/registrar flow | HITL | Complete | Reviewed schema, reviewed property atoms, 19-21 final checks depending on run, converged Cedar policy store. | Primary education case study; schema-repair extension. |
| CyberChair | Author/reviewer/chair conference-management flow | HITL | Complete | Reviewed schema, 42 reviewed final checks, converged Cedar policy store. | Noisy conference-management case study; many REDE labels collapse into one coherent policy store. |
| iTrust for Text2Policy | UC1/UC2/UC3/UC6/UC8/UC9 healthcare slice | HITL | Complete | Manually reviewed schema from r2, manually reviewed r4 property plan, 53 final checks, converged Cedar policy store. | Healthcare contrast; tests robustness of patient-specific relationship modeling. |
| iTrust for ACRE | Bounded healthcare slice across intro/glossary and selected UCs | HITL curated | Complete | Manually reviewed 97-atom schema plus typed-session repair, 82 reviewed final checks, converged Cedar policy store. | Largest REDE healthcare corpus; shows schema modeling and signal decomposition at healthcare scale. |
| Collected ACP Documents | Gradebook/RBAC sentence cluster | HITL | Complete | Manually reviewed schema/property atoms, 15 final checks, converged Cedar policy store. | Diverse sentence-level formalization stress test; shows mixed ACP corpora can be clustered into deployable mini-domains. |

## Current Results

These are the results currently available from AutoCedar run artifacts. The
counts below come from the local run directories, not from hand-entered chat
notes.

### IBM Course Management

Source/provenance:

```text
ibm use case/IBM Course Registration.txt
labelled data sets/IBM Course Management - ac rules.txt
labelled data sets/IBM Course Management.xlsx
```

Local REDE audit:

```text
401 sentence lines
169 access-control sentence lines
379 parsed NLACP triples
35 empty-subject triples
4 negated triples
```

| Run | Input and schema mode | Schema review | Property review | Schema gaps/repairs | Final checks | Stage 3 synthesis | Artifacts |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| Prior full HITL run | IBM course-registration prose; schema proposed from NL. | 44 proposed, 44 approved, 0 edits, 0 rejects. | 33 proposed, 21 approved, 12 rejected/repaired, 13 decisions with edit deltas. | 0 gaps, 0 repairs. | 21 checks, 19 reference policies. | `gpt-5.5`; converged in 1/20 iterations; final loss 0; 68.32s Stage 3 harness time; 7326 tokens; estimated $0.066. | `/tmp/autocedar-leap-human-runs/course-registration-human-review` |
| Semantic-boundary rerun | IBM course-registration prose; supplied reviewed schema from prior run, then allowed schema repair during property review. | Stage 1 not rerun in this pass. | 37 proposed, 19 approved, 18 rejected/repaired, 19 decisions with edit deltas. | 3 gaps, 3 repairs: explicit current/completed/upcoming semester hooks. | 19 checks, 19 reference policies. | `gpt-5.5`; converged in 2/20 iterations; final loss 0; first iteration hit a validation error, second passed 19/19; 73.46s Stage 3 harness time; 12131 tokens; estimated $0.0834. | `/tmp/autocedar-ibm-semantic-boundary-test/ibm-course-registration-semantic-boundary` |

Paper interpretation:

- IBM is the cleanest first case study: a coherent education domain with
  students, professors, registrars, semesters, course offerings, schedules,
  grades, report cards, and explicit authorization boundaries.
- The semantic-boundary rerun is important because it shows a realistic
  phenomenon: policy intent revealed that the reviewed schema still lacked
  explicit temporal/lifecycle hooks. AutoCedar repaired the schema before
  final synthesis instead of forcing the policy writer to approximate the
  missing concepts.
- For paper tables, report the prior full HITL run for end-to-end schema and
  property atomization, and report the semantic-boundary rerun as the schema
  repair ablation/extension.

### CyberChair

Source/provenance:

```text
CyberChair/CyberChair_source_document.txt
CyberChair/source_documents/overview.txt
labelled data sets/CyberChair - ac rules.txt
labelled data sets/CyberChair.xlsx
```

Local REDE audit:

```text
303 sentence lines
139 access-control sentence lines
386 parsed NLACP triples
187 empty-subject triples
0 negated triples
```

| Run | Input and schema mode | Schema review | Property review | Schema gaps/repairs | Final checks | Stage 3 synthesis | Artifacts |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| Full HITL run | CyberChair author/reviewer/chair prose; schema proposed from NL. | 55 proposed, 55 approved, 7 decisions with edit deltas, 0 rejects. | 48 proposed, 42 approved, 6 rejected/repaired, 7 decisions with edit deltas. | 1 gap, 1 repair: explicit authenticated/password-protected reviewer webpage context. | 42 checks, 42 reference policies. | `gpt-5.5`; converged in 1/20 iterations; final loss 0; passed 42/42 checks; 64.43s Stage 3 harness time; 8201 tokens; estimated $0.0663. | `/tmp/autocedar-cyberchair/run/cyberchair` |

Paper interpretation:

- CyberChair is a good noisy-domain stress test: the source labels have many
  empty-subject triples and many system-behavior statements, but the scenario
  still yields a coherent deployable Cedar schema and policy store after HITL
  filtering.
- The 42-check final plan shows that the result is not just a single direct
  NL-to-policy translation; the final candidate is constrained by a set of
  independently reviewed floor/ceiling/liveness-style signals.

### iTrust for Text2Policy

Source/provenance:

```text
Xiao Sources/iTrust for Text2Policy.txt
labelled data sets/iTrust for Text2Policy.txt
labelled data sets/iTrust for Text2Policy.xlsx
```

Local REDE audit:

```text
471 sentence lines
418 access-control sentence lines
1070 parsed NLACP triples
222 empty-subject triples
19 negated triples
```

Curated experiment spec:

```text
experiments/rede_autocedar/itrust_text2policy/spec.md
```

| Run | Input and schema mode | Schema review | Property review | Schema gaps/repairs | Final checks | Stage 3 synthesis | Artifacts |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| HITL `hitl-human-20260622-r4` with reviewed schema from `hitl-human-20260622-r2` | UC1/UC2/UC3/UC6/UC8/UC9 healthcare slice; schema proposed from NL in r2, then supplied to r4 for property review. | r2 schema: 73 proposed, 73 approved by manual semantic review. | r4 properties: 63 decisions; 53 approved final atoms, 10 rejected/repaired, 19 decisions with edit deltas. | 3 gaps, 3 repairs: login authentication evidence, prior/designated LHCP provider-list semantics, and provider search fields. Stage 1.75 corrected to empty unsat core after manually adding missing personal-representative type guards. | 53 checks, 53 reference policies. | `gpt-5.5`; converged in 2/20 iterations; iteration 1 loss 1/53, iteration 2 loss 0/53; 213.33s total harness time; 27784 tokens; estimated $0.2222. | `experiments/rede_autocedar/itrust_text2policy/runs/hitl-human-20260622-r4`; schema source `experiments/rede_autocedar/itrust_text2policy/runs/hitl-human-20260622-r2/stage1/final_schema.cedarschema` |
| AITL auto-accept `aitl-autoaccept-20260622-r3` | UC1/UC2/UC3/UC6/UC8/UC9 healthcare slice; schema proposed from NL. | 66 proposed, 66 approved by automated reviewer, 0 rejects. | 63 proposed, 43 approved, 20 rejected/repaired, 20 decisions with edit deltas. | 2 gaps, 2 repairs: patient MID/edit-field boundary and multi-hospital assignment multiplicity boundary. | 43 checks, 43 reference policies. | `gpt-5.5`; converged in 1/20 iterations; final loss 0; passed 43/43; 215.16s Stage 3 harness time; 17407 tokens; estimated $0.1934. | `experiments/rede_autocedar/itrust_text2policy/runs/aitl-autoaccept-20260622-r3` |
| AITL auto-accept diagnostic `aitl-autoaccept-20260622-r2` | UC1/UC2/UC3/UC6/UC8/UC9 healthcare slice; schema proposed from NL. | 68 proposed, 68 approved by automated reviewer. | 28 proposed, 28 decisions before stop; includes 3 schema-gap repairs and one classifier false-positive. | 3 real repairs before stop; stopped on `patient_can_undesignate_lhcp_for_self` because the classifier treated the phrase "property repair, not a schema gap" as a schema gap. | Not reached. | Not reached; `approved: false`. | `experiments/rede_autocedar/itrust_text2policy/runs/aitl-autoaccept-20260622-r2` |

Paper interpretation:

- The HITL r4 run is the paper-facing human-review result for this slice. It
  used the manually reviewed r2 schema, then manually reviewed/edit/rejected
  the property atoms in r4.
- The successful r3 run remains a useful AITL baseline. It should not be
  reported as human semantic review, but it shows that the current agentic
  reviewer can take a curated iTrust slice through schema atomization,
  property/signal atomization, schema repair, and convergent Stage 3 synthesis.
- Healthcare slices expose patient-specific relationships such as DLHCP and
  personal representative status. Those are exactly the kinds of semantic
  boundaries that a deployable policy language must not flatten into global
  roles.
- The stopped r2 run uncovered a general implementation bug in schema-gap
  classification. The fix treats explicit negations such as "not a schema gap"
  as property-repair signals, preventing the pipeline from adding duplicate
  schema structure when the schema already exposes the necessary relationship.

### iTrust for ACRE

Source/provenance:

```text
iTrust/iTrust_requirements_UTF8.txt
labelled data sets/iTrust for ACRE - ac rules.txt
labelled data sets/iTrust for ACRE.xlsx
```

Local REDE audit:

```text
1160 sentence lines
549 access-control sentence lines
2270 parsed NLACP triples
553 empty-subject triples
24 negated triples
```

Curated experiment spec:

```text
experiments/rede_autocedar/itrust_acre/spec.md
```

| Run | Input and schema mode | Schema review | Property review | Schema gaps/repairs | Final checks | Stage 3 synthesis | Artifacts |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| HITL curated `hitl-human-20260622-curated` | Bounded iTrust ACRE healthcare slice; schema proposed in AITL r2, manually inspected, then repaired for typed session ownership before curated HITL property plan. | 97 generated schema atoms manually accepted for the bounded slice, plus 1 manual schema repair replacing impossible `Session.user: User` with typed optional session-owner hooks. | 82 manually reviewed/curated final property checks; all accepted after comparing selected requirements, schema, and Cedar encodings. | Manual repair: typed session-owner hooks (`patientUser`, `hcpUser`, `lhcpUser`, `administratorUser`, `personalRepresentativeUser`, etc.) because Cedar entity hierarchy does not make `User` equalable with role-specific principals. All references passed `cedar validate` with 0 impossible-policy warnings. | 82 checks, 82 reference policies. | `gpt-5.5`; converged in 2/20 iterations; iteration 1 validation error, iteration 2 loss 0/82; 303.81s total harness time; 35311 tokens; estimated $0.3047. A mechanical floor-reference candidate also verified loss 0/82 in 0.86s. | `experiments/rede_autocedar/itrust_acre/runs/hitl-human-20260622-curated`; repaired schema `experiments/rede_autocedar/itrust_acre/reviewed_schema_with_typed_sessions.cedarschema` |
| AITL auto-accept diagnostic `aitl-autoaccept-20260622` | Bounded iTrust ACRE healthcare slice; schema proposed from NL. | 94 proposed, 94 approved by automated reviewer, 0 rejects. | 19 proposed, 12 approved, 7 rejected/repaired, 7 decisions with edit deltas. | 7 gaps found, 6 repairs applied, then stopped at repair budget. Gaps clustered around active-session hooks, personal-representative relationships, designated-LHCP diagnostic-information boundaries, and per-action schema hooks. | Not reached. | Not reached; stopped before Stage 1.75/final-plan/Stage 3 synthesis. | `experiments/rede_autocedar/itrust_acre/runs/aitl-autoaccept-20260622` |
| AITL auto-accept rerun `aitl-autoaccept-20260622-r2` | Same bounded iTrust ACRE healthcare slice after batched schema-repair prompt improvements; schema proposed from NL. | 97 proposed, 97 approved by automated reviewer, 0 rejects. | 71 proposed, 59 approved, 13 rejected/repaired, 12 decisions with edit deltas. | 2 gaps, 2 repairs: field-level credential selector for patient password/security-question secrecy; explicit hospital-list membership for administrator hospital assignment. Stage 1.75 unsat core empty. | 59 checks, 59 reference policies. | `gpt-5.5`; converged in 2/20 iterations; iteration 1 loss 29/59, iteration 2 loss 0/59; 284.86s total harness time; 52039 tokens; estimated $0.3409. | `experiments/rede_autocedar/itrust_acre/runs/aitl-autoaccept-20260622-r2` |

Paper interpretation:

- The HITL curated row is the paper-facing human-review result for this slice.
  It exposed a deeper schema modeling issue: Cedar entity hierarchy is not OO
  inheritance, so `Session.user: User` cannot be used as the owner field for
  `Patient`, `HCP`, `LHCP`, and other role-specific principal types. The
  reviewed schema repair made session ownership explicit with typed optional
  hooks.
- The first AITL diagnostic row is useful negative evidence, not a completed
  synthesis result. It exposed a real scaling issue for schema repair: global
  requirements such as active authenticated sessions and patient-specific
  relationships must be propagated across many actions. Repairing those hooks
  one action at a time exhausted the repair budget.
- The rerun shows the intended fix working. Stage 1 proposed a schema with
  reusable cross-cutting hooks, then Stage 2 discovered only two additional
  domain-specific gaps: field-level credential secrecy and hospital-list
  membership. After those repairs, Stage 3 produced a 399-line Cedar policy
  store that passed all 59 independently generated verifier checks.
- This is a strong paper datapoint for the "intent reveals schema gaps" claim:
  the system did not merely translate NLACP labels into policy clauses. It
  refined the schema until the reviewed healthcare intent could be expressed and
  checked compositionally.

### Collected ACP Documents

Source/provenance:

```text
Xiao Sources/Collected_ACP_Sentences.txt
labelled data sets/Collected ACP Sentences - ac rules.txt
labelled data sets/Collected ACP Sentences.xlsx
```

Local REDE audit:

```text
142 sentence lines
114 access-control sentence lines
258 parsed NLACP triples
5 empty-subject triples
39 negated triples
```

Curated experiment spec:

```text
experiments/rede_autocedar/collected_acp_gradebook/spec.md
```

| Run | Input and schema mode | Schema review | Property review | Schema gaps/repairs | Final checks | Stage 3 synthesis | Artifacts |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| HITL `hitl-human-20260622-r2` | Gradebook/RBAC slice from labelled sentence IDs 43-52; schema proposed from NL. | 15 proposed, 15 approved by manual semantic review, 0 rejects. | 19 decisions; 15 approved final atoms, 4 rejected/repaired, 5 decisions with edit deltas. | 1 gap, 1 repair: explicit `ExternalGrade.responsibleFaculty` hook for final-responsibility semantics. Stage 1.75 unsat core empty. | 15 checks, 15 reference policies. | `gpt-5.5`; converged in 2/20 iterations; final loss 0; 266.35s total harness time; 26062 tokens; estimated $0.2394. | `experiments/rede_autocedar/collected_acp_gradebook/runs/hitl-human-20260622-r2` |
| AITL auto-accept `aitl-autoaccept-20260622` | Gradebook/RBAC slice from labelled sentence IDs 43-52; schema proposed from NL. | 12 proposed, 12 approved by automated reviewer, 0 rejects. | 17 proposed, 14 approved, 3 rejected/repaired, 3 decisions with edit deltas. | 1 gap, 1 repair: explicit `ExternalGrade.responsibleFaculty` hook for final-responsibility semantics. Stage 1.75 unsat core empty. | 14 checks, 14 reference policies. | `gpt-5.5`; converged in 1/20 iterations; final loss 0; passed 14/14; 89.68s total harness time; 7798 tokens; estimated $0.08. | `experiments/rede_autocedar/collected_acp_gradebook/runs/aitl-autoaccept-20260622` |

Paper interpretation:

- Collected ACP is not a single coherent application requirements document; it
  is a mixed collection of access-control examples. The fair experiment is to
  isolate a coherent cluster, preserve the original sentence/provenance IDs,
  and test whether AutoCedar can turn that cluster into a deployable mini-domain.
- This slice is useful because it is dense with negative constraints:
  students/TAs must not assign or view external grades, and no role combination
  should both receive and assign external grades. The final 14-check plan
  includes those disjointness/ceiling-style signals alongside floors for
  successful grade and enrollment requests.
- The one schema repair is paper-relevant: "faculty take final responsibility"
  should not be approximated as a broad faculty-only assignment rule until the
  schema has an explicit responsibility hook. AutoCedar added that hook before
  final synthesis.

## Current Caveats

- These rows are evidence for **external-corpus formalization**, not proof
  that REDE labels are Cedar ground truth.
- The runs used scenario prose/slices derived from the REDE corpora. The
  iTrust and Collected ACP specs include selected source references; IBM and
  CyberChair still need their exact selected sentence IDs and NLACP triples
  copied into the paper-facing table.
- Manual semantic-review time was not separately recorded. The Stage 3 times
  above are harness synthesis times after review artifacts existed.
- The decision counts include critic-driven repair/replacement decisions; in
  the paper, distinguish "approved final atoms" from "rejected/repaired
  intermediate atoms."
- HITL rows now exist for iTrust for Text2Policy, iTrust for ACRE, and
  Collected ACP. AITL rows remain as baselines/diagnostics. Do not mix AITL and
  HITL results without labeling the reviewer mode.
- The iTrust ACRE diagnostic row is intentionally not a failure to hide. It is
  evidence that larger healthcare slices need batched cross-cutting schema
  repair for global session and patient-relationship boundaries. The HITL
  curated run is the completed human-reviewed result after typed session-owner
  schema repair.

## Remaining Table Work

| Item | Why |
| --- | --- |
| IBM exact provenance backfill | Copy selected sentence IDs and selected NLACP triples into this tracker or a paper appendix, matching the style of the iTrust/Collected ACP specs. |
| CyberChair exact provenance backfill | Copy selected sentence IDs and selected NLACP triples into this tracker or a paper appendix, matching the style of the iTrust/Collected ACP specs. |
| Manual effort logging | Future HITL reruns should record semantic-review time and number of human questions/edits separately from Stage 3 harness time. |

## Paper-Ready Claim Boundary

The clean claim is:

> Given real NLACP scenario material, AutoCedar helps a human convert
> natural-language access-control intent into HITL-reviewed Cedar schemas,
> HITL-reviewed verifier signals, and a final Cedar policy store that converges
> against those signals.

Do not claim that ACRE/REDE directly evaluates Cedar correctness. It evaluates
whether AutoCedar can bridge from realistic access-control requirements and
weak NLACP extraction labels to deployable, verifier-backed Cedar artifacts.
