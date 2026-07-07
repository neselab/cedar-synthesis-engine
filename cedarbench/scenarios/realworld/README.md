# CedarBench Realworld Scenarios

Hand-designed Cedar policy scenarios targeting production-use patterns
and specific verification-harness capabilities. Each scenario has a
natural-language `policy_spec.md`, a `schema.cedarschema`, a
`verification_plan.py` defining the checks the harness runs against a
synthesized candidate, and a `references/` directory of per-check
Cedar policy bounds.

This directory is companion to, and conceptually distinct from, the
auto-generated mutation scenarios in `cedarbench/scenarios/<domain>_*`.
The mutation scenarios are produced by a templated generator that
varies a base policy in structured ways; the realworld scenarios are
designed by hand to probe production patterns and harness edge cases.

## Scenario Index

| # | Scenario | Pattern | Difficulty | Novel Cedar feature / harness target |
|---|----------|---------|:----------:|--------------------------------------|
| 1 | [emergency_break_glass](./emergency_break_glass) | Emergency override with care-team baseline | medium | Narrow break-glass permit that unlocks only view, not edit |
| 2 | [approval_chain_workflow](./approval_chain_workflow) | Multi-signer approval state machine | medium | `set.containsAll()` for unanimous-consent gating |
| 3 | [multi_tenant_saas](./multi_tenant_saas) | Tenant isolation with global-support read path | medium | Narrow cross-tenant read with context attestation |
| 4 | [contextual_mfa_elevation](./contextual_mfa_elevation) | Step-up authentication | medium | `datetime.durationSince()` for MFA freshness |
| 5 | [legal_hold_override_expiry](./legal_hold_override_expiry) | Records management with conditional override | medium | Override interplay: legal hold extends edit past expiry |
| 6 | [delegation_temporary_grant](./delegation_temporary_grant) | Ephemeral grants via context attestation | medium | Optional context attribute with `has` guarding |
| 7 | [pii_data_classification](./pii_data_classification) | MLS / compartmentalization | medium | String-enum hierarchy + orthogonal forbid gates |
| 8 | [payroll_separation_of_duties](./payroll_separation_of_duties) | SOX Separation of Duties | medium | `principal != resource.initiator` + amount-threshold escalation |
| 9 | [api_key_scoped_access](./api_key_scoped_access) | Machine-to-machine authorization | medium | Non-User principal (`ApiKey`) + scope strings |
| 10 | [string_prefix_domain_match](./string_prefix_domain_match) | Email-pattern ACL | medium | Cedar's `like` glob operator (only string primitive) |
| 11 | [intentional_planner_contradiction](./intentional_planner_contradiction) | §8.8 regression test | hard (planning) | Self-referential corner case hunting unsatisfiable bounds |
| 12 | [hundred_check_scale](./hundred_check_scale) | Large-scale RBAC matrix | hard (scale) | 157-check stress test for conversation trimming and context |
| 13 | [nested_namespaces](./nested_namespaces) | Multi-level namespace organization | medium | Three-level namespace with cross-namespace entity type references |
| 14 | [deep_entity_hierarchy](./deep_entity_hierarchy) | 5-level transitive membership | medium | Deepest entity `in` chain in the benchmark |
| 15 | [policy_annotations](./policy_annotations) | @id / @description annotations | easy | Cedar annotation syntax on policy rules |
| 16 | [set_contains_any](./set_contains_any) | Tag-based access with containsAny | medium | `.containsAny()` set operation (first use) |
| 17 | [gdpr_data_retention](./gdpr_data_retention) | GDPR retention + right-to-erasure | hard | Datetime comparison for retention expiry + erasure flag |
| 18 | [audit_log_immutability](./audit_log_immutability) | Append-only audit log | medium | Asymmetric action permissions (append OK, delete forbidden) |
| 19 | [content_moderation_escalation](./content_moderation_escalation) | Tiered moderation with trust levels | medium | Numeric trust-level vs severity threshold matching |
| 20 | [resource_budget_enforcement](./resource_budget_enforcement) | Quota-based provisioning | medium | Numeric comparison for tier-derived resource limits |
| 21 | [backup_restore_asymmetric](./backup_restore_asymmetric) | Asymmetric backup/restore | medium | Environment-based restriction + on-call boolean |
| 22 | [iot_device_auth](./iot_device_auth) | IoT device authorization | medium | Non-User Device principal + capability set |
| 23 | [conference_room_booking](./conference_room_booking) | Time-windowed room booking | medium | Datetime + numeric capacity + level comparison |
| 24 | [group_chat_moderator](./group_chat_moderator) | Discord/Slack-style moderation | medium | Owner/moderator/member tiers with `Set.contains()` |
| 25 | [incident_response_war_room](./incident_response_war_room) | Tiered incident escalation | hard | Severity-clearance threshold + post-mortem override |
| 26 | [educational_gradebook](./educational_gradebook) | Teacher/student/parent visibility | medium | Optional `parentOf` context with `has` guarding |
| 27 | [medical_prescription_workflow](./medical_prescription_workflow) | Controlled substance prescription | hard | Optional `controlledSubstanceVerified` + multi-role workflow |
| 28 | [loan_approval_workflow](./loan_approval_workflow) | Multi-tier banking approval | hard | Numeric `approvalLimit` + risk-based director escalation |
| 29 | [matter_based_legal_access](./matter_based_legal_access) | Law firm matter-based access | medium | `Set.contains()` for matter assignment + privileged doc gate |
| 30 | [shared_inbox_delegation](./shared_inbox_delegation) | Multi-user shared mailbox | medium | Owner/delegate/member tiers with `Set.contains()` |
| 31 | [data_lineage_ancestry](./data_lineage_ancestry) | Clearance-based data lineage | hard | Classification hierarchy + department-scoped + PII export restriction |
| 32 | [webhook_signature_verification](./webhook_signature_verification) | Outbound M2M webhook delivery | medium | Non-User `WebhookEndpoint` principal + `Set.contains()` for event filtering |
| 33 | [time_of_day_business_hours](./time_of_day_business_hours) | Time-of-day business hours | medium | Numeric hour comparison for time restriction + role override |
| 34 | [feature_flag_rollout](./feature_flag_rollout) | Feature flag gradual rollout | medium | Numeric `rolloutBucket < rolloutPercentage` + boolean `isEnabled` |
| 35 | [document_versioning_lock](./document_versioning_lock) | Document locking with versioning | medium | `lockedBy == principal` lock-owner bypass + draft-state gate |
| 36 | [multi_factor_resource_unlock](./multi_factor_resource_unlock) | Graduated MFA unlock | hard | Multiple boolean context attestations × sensitivity level |
| 37 | [rate_limit_by_role](./rate_limit_by_role) | API rate limiting by tier | medium | Numeric tier-derived quotas + context-provided request counter |
| 38 | [customer_support_ticket_escalation](./customer_support_ticket_escalation) | Support ticket escalation | medium | Numeric `maxPriority >= priority` + escalation lock |
| 39 | [inventory_warehouse_zone](./inventory_warehouse_zone) | Warehouse zone access | medium | Zone-string matching + hazardous material supervisor gate |
| 40 | [ci_cd_deployment_gate](./ci_cd_deployment_gate) | CI/CD deployment authorization | medium | Environment-tiered deploy + test-pass boolean gate |
| 41 | [subscription_content_gate](./subscription_content_gate) | Subscription-based content | medium | Plan-tier hierarchy + preview bypass |
| 42 | [compliance_training_gate](./compliance_training_gate) | Compliance training prerequisite | medium | `Set.containsAll()` for training completion + sensitive export restriction |
| 143 | [ultra_ibm_course_registration](./ultra_ibm_course_registration) | Corpus-derived university course registration | ultra-hard | Reviewed schema + property target from IBM/REDE-style requirements |
| 144 | [ultra_cyberchair](./ultra_cyberchair) | Corpus-derived conference management | ultra-hard | Review lifecycle, conflicts of interest, staged visibility, PCC monitoring |
| 145 | [ultra_itrust_full_nl](./ultra_itrust_full_nl) | Corpus-derived healthcare access control | ultra-hard | Full iTrust NL intent with reviewed schema/property atoms |
| 146 | [ultra_itrust_acre](./ultra_itrust_acre) | iTrust ACRE-derived healthcare access control | ultra-hard | ACRE-style source formalized into Cedar target |
| 147 | [ultra_itrust_text2policy](./ultra_itrust_text2policy) | iTrust Text2Policy-derived healthcare access control | ultra-hard | Text2Policy-style source formalized into Cedar target |

## Pattern Taxonomy

### Identity & authorization patterns
- **Care-team / ACL** — emergency_break_glass (1), legal_hold_override_expiry (5)
- **Ephemeral delegation** — delegation_temporary_grant (6)
- **Tenant isolation** — multi_tenant_saas (3)
- **Role-based access (RBAC)** — payroll_separation_of_duties (8), hundred_check_scale (12), policy_annotations (15)
- **Multi-level security (MLS)** — pii_data_classification (7), data_lineage_ancestry (31)
- **Machine-to-machine** — api_key_scoped_access (9), iot_device_auth (22), webhook_signature_verification (32)
- **Email / pattern-based ACL** — string_prefix_domain_match (10)
- **Matter / case-based** — matter_based_legal_access (29)
- **Shared resource delegation** — shared_inbox_delegation (30), group_chat_moderator (24)
- **Subscription / entitlement** — subscription_content_gate (41), feature_flag_rollout (34)
- **Multi-factor unlock** — multi_factor_resource_unlock (36)

### Temporal & contextual patterns
- **Step-up authentication** — contextual_mfa_elevation (4)
- **Document expiry** — legal_hold_override_expiry (5), gdpr_data_retention (17)
- **Emergency time-windows** — emergency_break_glass (1)
- **Grant expiry** — delegation_temporary_grant (6)
- **Room booking** — conference_room_booking (23)
- **Business hours** — time_of_day_business_hours (33)

### Workflow / state-machine patterns
- **Multi-signer approval** — approval_chain_workflow (2)
- **SOX Separation of Duties** — payroll_separation_of_duties (8)
- **Medical prescription** — medical_prescription_workflow (27)
- **Loan approval** — loan_approval_workflow (28)
- **Support ticket escalation** — customer_support_ticket_escalation (38)
- **CI/CD deployment** — ci_cd_deployment_gate (40)

### Compliance patterns
- **GDPR** — gdpr_data_retention (17)
- **Audit immutability** — audit_log_immutability (18)
- **Content moderation** — content_moderation_escalation (19)
- **Budget enforcement** — resource_budget_enforcement (20)
- **Backup/restore asymmetry** — backup_restore_asymmetric (21)
- **Incident response** — incident_response_war_room (25)
- **Training prerequisite** — compliance_training_gate (42)
- **Rate limiting** — rate_limit_by_role (37)

### Resource management patterns
- **Document locking** — document_versioning_lock (35)
- **Warehouse zones** — inventory_warehouse_zone (39)

### Structural / Cedar-feature patterns
- **Deep hierarchy** — deep_entity_hierarchy (14), nested_namespaces (13)
- **Policy annotations** — policy_annotations (15)
- **Set operations** — set_contains_any (16), approval_chain_workflow (2), compliance_training_gate (42)

### Meta / harness-stress patterns
- **§8.8 regression test** — intentional_planner_contradiction (11)
- **Scale stress** — hundred_check_scale (12)

### Corpus-derived ultra-hard scenarios
- **Education / course registration** — ultra_ibm_course_registration (143)
- **Conference management** — ultra_cyberchair (144)
- **Healthcare / iTrust** — ultra_itrust_full_nl (145), ultra_itrust_acre (146), ultra_itrust_text2policy (147)

## Cedar Features Exercised (First Appearance)

| Cedar feature | Scenario introducing it |
|---|---|
| `set.containsAll()` | approval_chain_workflow |
| `set.containsAny()` | set_contains_any |
| `datetime.durationSince(other)` | contextual_mfa_elevation |
| `like` glob operator | string_prefix_domain_match |
| Non-User principal entity type | api_key_scoped_access |
| Multiple non-User principal types | iot_device_auth |
| `@id()` / `@description()` annotations | policy_annotations |
| 5-level entity hierarchy | deep_entity_hierarchy |
| Multi-level namespaces | nested_namespaces |
| Optional context attribute `?` with `has` guarding | delegation_temporary_grant |

## Current Results

All 42 scenarios converge under the post-fix harness (see
`docs/harness_fix_log.md` for the harness evolution):

| Scenario | Iters | Checks | Cost |
|----------|:-----:|:------:|:----:|
| emergency_break_glass            | 1  | 7   | $0.003 |
| approval_chain_workflow          | 2  | 16  | $0.009 |
| multi_tenant_saas                | 3  | 10  | $0.011 |
| contextual_mfa_elevation         | 2  | 13  | $0.008 |
| legal_hold_override_expiry       | 1  | 11  | $0.003 |
| delegation_temporary_grant       | 2  | 12  | $0.008 |
| pii_data_classification          | 2  | 8   | $0.010 |
| payroll_separation_of_duties     | 1  | 15  | $0.004 |
| api_key_scoped_access            | 2  | 14  | $0.009 |
| string_prefix_domain_match       | 2  | 8   | $0.006 |
| intentional_planner_contradiction | 1  | 4   | $0.003 |
| hundred_check_scale              | 2  | 157 | $0.021 |
| nested_namespaces                | 2  | 10  | $0.007 |
| deep_entity_hierarchy            | 1  | 11  | $0.003 |
| policy_annotations               | 1  | 9   | $0.003 |
| set_contains_any                 | 2  | 9   | $0.006 |
| gdpr_data_retention              | 2  | 12  | $0.006 |
| audit_log_immutability           | 1  | 9   | $0.003 |
| content_moderation_escalation    | 10 | 12  | $0.043 |
| resource_budget_enforcement      | 1  | 12  | $0.003 |
| backup_restore_asymmetric        | 2  | 10  | $0.006 |
| iot_device_auth                  | 2  | 10  | $0.006 |
| conference_room_booking          | 2  | 9   | $0.005 |
| group_chat_moderator             | 2  | 14  | $0.006 |
| incident_response_war_room       | 2  | 13  | $0.007 |
| educational_gradebook            | 2  | 15  | $0.008 |
| medical_prescription_workflow    | 2  | 17  | $0.009 |
| loan_approval_workflow           | 2  | 16  | $0.008 |
| matter_based_legal_access        | 1  | 11  | $0.003 |
| shared_inbox_delegation          | 1  | 12  | $0.003 |
| data_lineage_ancestry            | 3  | 12  | $0.012 |
| webhook_signature_verification   | 1  | 9   | $0.003 |
| time_of_day_business_hours       | 2  | 8   | $0.007 |
| feature_flag_rollout             | 2  | 10  | $0.006 |
| document_versioning_lock         | 2  | 11  | $0.007 |
| multi_factor_resource_unlock     | 2  | 10  | $0.008 |
| rate_limit_by_role               | 2  | 8   | $0.007 |
| customer_support_ticket_escalation | 2 | 13  | $0.007 |
| inventory_warehouse_zone         | 3  | 11  | $0.010 |
| ci_cd_deployment_gate            | 3  | 11  | $0.010 |
| subscription_content_gate        | 2  | 10  | $0.008 |
| compliance_training_gate         | 2  | 9   | $0.007 |

Phase 1 in every scenario is hand-authored; Phase 2 is Haiku 4.5.

## Citation

If you use these scenarios in academic work, please cite as:

```
CedarBench-Realworld: Hand-designed Cedar policy scenarios for
verification-harness evaluation. Part of the Cedar Synthesis Engine
repository. https://github.com/neselab/cedar-synthesis-engine
```
