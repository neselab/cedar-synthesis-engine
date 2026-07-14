# AGENTS.md — Cedar Synthesis Engine

Project orientation for future Codex sessions. This file auto-loads.
Keep it under ~300 lines; move deep detail to `docs/`.

## ⚠️ CURRENT DIRECTION (May 2026)

**The project is pivoting to a Human-in-the-Loop production agent.** The
existing v1 harness and 221-scenario CedarBench are now the "Phase 0"
baseline. The next major work is a HITL agent that handles real
production inputs (prose specs from regulations, memos, etc.) by
atomizing schema design and property elicitation with user validation.

**Read before doing anything new:** `docs/HITL_PRODUCTION_AGENT_PLAN.md`.
That document is a complete handoff for the HITL agent work.

If you're a fresh Codex instance picking up this project, the
recommended first step is the **honest scenario-difficulty grading task
(Step A in the plan)** — don't write new scenarios or polish the paper
until that's done.

## Non-negotiable HITL validation rule

Do **not** simulate human semantic HITL approval with a scripted reviewer and
present that as validation. Automated TUI drivers may test plumbing only:
paste handling, action routing, progress rendering, and backend invocation.

Semantic HITL review means manually comparing the full natural-language
requirements, the proposed atom, and the Cedar encoding/action semantics. Only
approve, edit, or reject based on whether that atom is actually wanted by the
requirements. This is central to AutoCedar's research claim: human intent
verification cannot be replaced by brittle name-matching, alias lists, or other
hidden heuristics.

## What this project is

A two-phase CEGIS harness that synthesizes Cedar access-control policies
from natural-language specifications. Phase 1 (planner) produces a
verification plan + reference policies (ceilings/floors/liveness); Phase 2
(synthesizer, small model = Haiku 4.5) iteratively proposes candidates
checked by `cedar symcc` + `cedar validate`. The central thesis: a
structured signal layer uplifts a small cheap model into producing correct
Cedar at production cost.

Two artifacts are being built:
1. **CedarBench** — a large benchmark of Cedar policy scenarios
   (`cedarbench/scenarios/`). First large-scale Cedar evaluation dataset.
2. **The harness** — `eval_harness.py` + `orchestrator.py` + `solver_wrapper.py`,
   documented as eleven novel contributions in `docs/harness_fix_log.md`.

We are targeting **two papers**:
- **Workshop paper** — CedarBench as a dataset (target ≥120 scenarios).
  Venue: LangSec or PLAS.
- **Main-track paper** — the harness + its signal-layer contributions.

## Key files and directories

```
eval_harness.py          # main CLI entry (run_scenario, main, CEGIS loop)
orchestrator.py          # per-check verification orchestration
solver_wrapper.py        # cedar validate / cedar symcc invocation
                         # CEDAR defaults to ~/.cargo/bin/cedar; env-overridable
docs/harness_fix_log.md  # READ FIRST — §3–§8 document all harness rules
                         # §8.1–§8.11 = the eleven novel contributions
docs/cegis_algorithm.md  # high-level CEGIS algorithm description
cedarbench/scenarios/    # 79 mutation scenarios (e.g. github_*, clinical_*)
cedarbench/scenarios/realworld/  # hand-designed production patterns
cedarbench/scenarios/realworld/README.md  # dataset index / taxonomy / citation
cedarbench/README.md     # top-level dataset README
```

## Scenario file layout

Every scenario (mutation OR realworld) is a directory with exactly:
```
policy_spec.md         # NL spec with YAML frontmatter (realworld only, so far)
schema.cedarschema     # Cedar schema defining entities/actions/context
verification_plan.py   # get_checks() returning list of dicts
references/*.cedar     # one per check: ceiling/floor reference bounds
```

Realworld `policy_spec.md` frontmatter:
```yaml
---
pattern: <short pattern name>
difficulty: easy | medium | hard | hard (planning)
features:
  - <feature 1>
  - <feature 2>
domain: <vertical>
---
```

Check types in `verification_plan.py`:
- `implies` — ceiling: candidate ⇒ reference. Candidate must be NO MORE permissive.
- `floor` — candidate ⇐ reference. Candidate must be AT LEAST as permissive.
- `always-denies-liveness` — at least one request must be permitted.

## Running a scenario

The harness uses Codex OAuth by default. Run `codex login` once, then run
via `uv`:

```bash
uv run python eval_harness.py \
  --scenario cedarbench/scenarios/realworld/<name> \
  --no-review \
  --model gpt-5.5 \
  --max-iters 20
```

Anthropic remains supported only as an explicit opt-in via
`AUTOCEDAR_PROVIDER=anthropic` plus `ANTHROPIC_API_KEY`.

Output lands in `eval_runs/<timestamp>/`. Exit code is informational.

**Worktree note:** git worktrees don't share `.env`. Symlink it in
from the main repo root once per worktree:
`ln -s /path/to/main-repo/.env .env`. The symlink is gitignored.

## Authoring workflow (Phase 1 manually, Phase 2 = Haiku)

Since streaming, **Phase 1 is done by hand** (Codex acting as security
engineer), not by an API call. The scenario's references + verification_plan
constitute the "plan." Phase 2 is Haiku under test — if Haiku stalls,
the bug is in the harness signal layer, not the model.

Per-scenario checklist:
1. Write `policy_spec.md` with YAML frontmatter and unambiguous requirements.
2. Write `schema.cedarschema`. Validate it: `cedar validate --schema X --policies /dev/null`.
3. Write `verification_plan.py` enumerating ceilings + floors + liveness.
4. Write one `references/<check_name>.cedar` per non-liveness check.
5. Validate every reference: `cedar validate --schema X --policies references/Y.cedar`.
6. Run the harness. Expect convergence in 1–3 iters if rules below are followed.
7. If Haiku stalls: investigate whether it's a missing harness signal (new
   §8.x contribution) or a genuine spec problem. Never lower the bar.

## Phase 1 planning rules (condensed from harness_fix_log.md)

These are the rules you, as the planner, must follow when writing references.
Breaking them reproduces known failure modes from §8.x.

**§8.6 Role-intersection trap.** Cedar entities can be in MULTIPLE roles.
"Role X is blocked from R" should NOT be encoded as `forbid when principal in
Role::"X"` because a user in both X and Y hits the forbid even if Y's floor
permits them. Correct encoding: exclude R from the permit for X.

**§8.8 Floor-bound consistency.** Every floor must be jointly satisfiable with
every global forbid / sibling ceiling. When writing a floor, walk every global
forbid in the spec and add `!global_forbid_condition` exclusions to the floor's
`when` clause. Example: a `floor_owner_read` should say
`principal == resource.owner && !(principal in resource.owner.blocked) && ...`,
not just `principal == resource.owner`.

**§8.9 Cedar datetime/duration syntax.** `datetime("...")` uses ISO 8601
(`"2025-03-02T20:00:00Z"`); `duration("...")` uses **Go-style**
(`"21h"`, `"-24h"`, `"1h30m"`, `"1d"`) and REJECTS ISO 8601 (`"PT21H"`, `"P1D"`).

**Negated-`has` trap (§5.4/§8.3).** Cedar's type-checker does NOT propagate
negation through `has`. Writing `!(context has targetUser) || context.targetUser.role == "X"`
is rejected. Correct guard:
`(!(context has targetUser) || (context has targetUser && context.targetUser.role == "X"))`.

**Optional attributes.** Declared with `?` in schema. MUST be `has`-guarded
before any read. `context has activeGrant && context.activeGrant.grantee == principal`.

**Property-based plans (§5.2).** References encode orthogonal properties
(e.g. "target must be same org," "approver role must be ≥ manager"), not
per-role splits. Bounds compose via conjunction.

**§8.10 Entity-graph membership liveness.** `cedar symcc` cannot prove
liveness for `principal in resource` (entity-graph membership). The entity
graph is opaque to the symbolic analyzer. Use `resource.members.contains(principal)`
with `members: Set<Entity>` on the resource instead — symcc can reason about
set containment. Discovered on `group_chat_moderator`.

**Symbolic-analysis limits.** `cedar symcc` ignores Cedar `template`-linked
policies — they appear as empty to the analyzer. Do NOT write scenarios
that rely on templates for verification; use the delegation pattern
(optional context attribute pre-validated by the host app) as the workaround.

## Commit hygiene

- Commits for scenarios go as batches of 3–6 related additions.
- **Commit before moving to the next batch** — the previous session lost
  ~1 scenario's work to a crash mid-batch. Don't hold work uncommitted for
  long stretches.
- Commit message style: `Add N <pattern> realworld scenarios (...)` or
  `Update harness_fix_log: §X.Y <contribution>`.

## Dataset state (update on every commit)

**Total scenarios: 221** (79 mutation + 142 realworld)
**Tested PASS so far: 121/121** original benchmark (committed before v2 extension).
**Untested: 100 v2-extension hard scenarios** (built but not yet run through
harness — done in 10 batches per `cedarbench/PROPOSED_HARD_SCENARIOS.md`).

**Original 121:** github 14, clinical 11, doccloud 10, streaming 10, tax 8,
hotel 9, sales 9, tags 8, realworld 42. Total cost: ~$13.30.

**v2 extension (100 scenarios, batches in `PROPOSED_HARD_SCENARIOS.md`):**
- Batch 1 (Cedar features): entity_tags_with_hastag, decimal_currency_comparison,
  ipaddr_corporate_network, if_then_else_decision_tree, five_way_role_intersection,
  recurring_maintenance_window, hipaa_minimum_necessary, mega_scale_500_checks,
  adversarial_oscillation_bait, regression_battery_all_traps
- Batch 2 (temporal+adversarial): age_verification_leap_years, anti_transitive_delegation,
  four_level_unless_chain, n_of_m_signature_withdrawal, sox_three_role_sod,
  itar_us_persons_only, like_with_escape_chars, reserved_keyword_attr_name,
  deceptive_progress_signal, oop_prior_trap
- Batch 3 (compliance): ferpa_age_18_transition, pci_dss_cde_boundary,
  gdpr_purpose_limitation, coppa_under_13, aml_kyc_tiered, gdpr_dpia_required,
  purpose_bound_field_access, compound_attestation_multi_signer,
  stale_cache_invalidation, quorum_attestation
- Batch 4 (Cedar feature completion): ipaddr_ipv6_mixed, enumerated_status_entity,
  common_type_definitions, union_principal_types, action_group_multi_inheritance,
  long_arithmetic_overflow_avoidance, decimal_precision_boundary,
  empty_set_vacuous_truth, homogeneous_set_type_mismatch, action_without_resource_applies_to
- Batch 5 (temporal complexity): rolling_rate_limit_window, business_hours_user_timezone,
  multi_cert_chain_validity, delegation_chain_expiry_dual, cascading_session_expiry,
  embargo_by_region, duration_arithmetic_composition, recurring_weekly_blackout,
  time_decay_permissions, grace_period_three_tier
- Batch 6 (role advanced): three_way_mutual_exclusion, context_scoped_admin,
  role_elevation_with_attestation, hierarchical_override_three_levels,
  priority_based_role_resolution, cert_required_role_activation,
  role_composition_from_attributes, dual_owner_joint_consent,
  conditional_role_activation, role_set_intersection_required
- Batch 7 (conflict precedence): five_orthogonal_forbids, default_scope_mismatch,
  exception_to_exception_emergency, conflicting_attestation_sources,
  whitelist_and_blacklist, union_semantics_adversarial,
  forbid_with_specific_exception, revocation_cascade_reinstatement,
  multi_forbid_floor_consistency, ordered_override_resolution
- Batch 8 (scale stress): mega_scale_1000_checks, twenty_action_workflow,
  fifty_role_matrix, ten_level_hierarchy, five_namespace_coordination,
  long_permit_25_conditions, fifteen_optional_context, wide_set_50_elements,
  hundred_tenant_isolation, action_with_many_principals
- Batch 9 (planner traps): ambiguous_spec_most_restrictive,
  contradicting_requirements_literal, missing_edge_case_empty_set,
  implicit_deny_by_default, partial_spec_pattern_extrapolation,
  counterintuitive_admin_no_edit, priority_ordered_requirements,
  tacit_domain_convention, redundant_spec_single_rule, hypothetical_exception_unspecified
- Batch 10 (meta adversarial): plateau_landscape_many_equal, red_herring_attributes,
  hidden_simple_gotcha, specification_ambiguity_needs_counterexample,
  five_equivalent_formulations, decoy_trivial_properties,
  causal_predecessor_chain, nonce_replay_prevention, quiescence_window,
  inverted_default_permit

Cedar findings discovered while building v2:
- §8.3 negated-has trap also applies to `hasTag`
- duration has no +/- arithmetic; use `.toMilliseconds()` + Long arithmetic
- Reserved keyword attrs: `in`, `has`, `like`, `if`, `then`, `else`, `is` REJECTED;
  `permit`, `forbid`, `principal`, `action`, `resource`, `when`, `unless` ACCEPTED
- Cedar accepts `entity Status enum [...]` syntax
- Common types support nested aliases (`type X using type Y`)
- Actions cannot have empty resource list — use sentinel entities
- Namespace + entities + actions must all be in single block per namespace name
- `__cedar::` namespace rejected at lexer level

Realworld scenarios (31, all PASS):
1. emergency_break_glass — PASS
2. approval_chain_workflow — PASS
3. multi_tenant_saas — PASS
4. contextual_mfa_elevation — PASS
5. legal_hold_override_expiry — PASS
6. delegation_temporary_grant — PASS
7. pii_data_classification — PASS
8. payroll_separation_of_duties — PASS
9. api_key_scoped_access — PASS
10. string_prefix_domain_match — PASS
11. intentional_planner_contradiction — PASS
12. hundred_check_scale — PASS (157 checks)
13. nested_namespaces — PASS 2 iters
14. deep_entity_hierarchy — PASS 1 iter (one-shot)
15. policy_annotations — PASS 1 iter (one-shot)
16. set_contains_any — PASS 2 iters
17. gdpr_data_retention — PASS 2 iters
18. audit_log_immutability — PASS 1 iter
19. content_moderation_escalation — PASS 10 iters (hardest)
20. resource_budget_enforcement — PASS 1 iter
21. backup_restore_asymmetric — PASS 2 iters
22. iot_device_auth — PASS 2 iters
23. conference_room_booking — PASS 2 iters
24. group_chat_moderator — PASS 2 iters
25. incident_response_war_room — PASS 2 iters
26. educational_gradebook — PASS 2 iters
27. medical_prescription_workflow — PASS 2 iters
28. loan_approval_workflow — PASS 2 iters
29. matter_based_legal_access — PASS 1 iter
30. shared_inbox_delegation — PASS 1 iter
31. data_lineage_ancestry — PASS 3 iters
32. webhook_signature_verification — PASS 1 iter
33. time_of_day_business_hours — PASS 2 iters
34. feature_flag_rollout — PASS 2 iters
35. document_versioning_lock — PASS 2 iters
36. multi_factor_resource_unlock — PASS 2 iters
37. rate_limit_by_role — PASS 2 iters
38. customer_support_ticket_escalation — PASS 2 iters
39. inventory_warehouse_zone — PASS 3 iters
40. ci_cd_deployment_gate — PASS 3 iters
41. subscription_content_gate — PASS 2 iters
42. compliance_training_gate — PASS 2 iters

## Known symcc limitations

- **Entity-graph `in` membership:** `cedar symcc` cannot prove liveness
  for `principal in resource` (entity-graph membership). Use attribute-based
  `resource.members.contains(principal)` instead. Discovered in
  `group_chat_moderator`.
- **Cedar templates:** `cedar symcc` ignores template-linked policies.
  Use optional context attributes as the workaround for delegation patterns.

## Remaining opportunities

**Metadata backfill** — add YAML frontmatter to the 79 mutation scenarios
(pattern / difficulty / features / domain), for dataset filterability.

**Additional Tier C adversarial:** mega_scale_500, ambiguous_spec_guidance,
redundant_rules, missing_liveness_trap — defer unless harness paper needs
ablation data.

## User collaboration notes

- The user is publishing this as a dataset contribution to the community.
- **Breadth over depth** — coverage of real-world patterns > deep harness
  testing, within reason.
- The user's session tends to hit "prompt is too long" errors on very long
  runs. Be disciplined about committing.
- Do not batch commits beyond a handful of scenarios. Preserve progress.
