# CedarBench Mutation Plan

## 1. Base Scenario Analysis

### 1.1 GitHub Repository Permissions (`experiments/github/`)
| Aspect | Detail |
|--------|--------|
| **Cedar features** | Entity group membership (`in resource.readers`), cross-entity traversal (Issue→Repo), entity equality (`principal == resource.reporter`), boolean attribute (`isArchived`), action groups, forbid/permit interaction |
| **Pattern** | Hierarchical RBAC with forbid override |
| **Schema** | 6 entity types, 11 actions, 5 role tiers (Reader→Admin), Repository has 5 UserGroup attrs + Bool |
| **Complexity** | 8 permit + 1 forbid; 3-level entity chain (Issue→Repo→UserGroup) |
| **Synthesis challenge** | Dual-path auth (Writer OR Reporter for edit/delete), archive forbid must not block reads |

### 1.2 Document Cloud (`dataset/document_cloud/`)
| Aspect | Detail |
|--------|--------|
| **Cedar features** | Set membership (`in resource.viewACL`), `has` on optional attrs, `.contains()` on sets, Public principal type, `unless` clauses, context field (`is_authenticated`) |
| **Pattern** | Fine-grained ABAC with ACL + public sharing + mutual blocking |
| **Schema** | 6 entity types, 10 actions, Document has owner/ACLs/publicAccess/isPrivate, User has blocked set |
| **Complexity** | 11 permit + 2 forbid; set containment + string enum (`publicAccess`) |
| **Synthesis challenge** | Multiple auth paths (owner/ACL/public), bidirectional blocking, authentication guard |

### 1.3 Hotel Chains — Static (`dataset/hotel_chains/static/`)
| Aspect | Detail |
|--------|--------|
| **Cedar features** | Hierarchical entity membership (`Property in [Hotel]`), complex record types (`PermissionsMap`), set containment (`resource in principal.hotelAdminPermissions`), `is` type check |
| **Pattern** | Role-scoped hierarchical ABAC with resource-type segmentation |
| **Schema** | 4 entity types (User, Hotel, Property, Reservation), 12 actions, PermissionsMap record type |
| **Complexity** | ~9 permit; 3-level hierarchy (Hotel→Property→Reservation) |
| **Synthesis challenge** | Hierarchical inheritance, resource-type segmentation (viewer/member/admin × reservation/property/hotel) |

### 1.4 Sales Organizations — Static (`dataset/sales_orgs/static/`)
| Aspect | Detail |
|--------|--------|
| **Cedar features** | Job entity enum, action groups (InternalPrezViewActions etc.), forbid with conditions, context-dependent auth (`context.target`), optional context fields |
| **Pattern** | Hybrid RBAC+ABAC with job-based segmentation and market grouping |
| **Schema** | 5 entity types (User, Job, Market, Presentation, Template), ~14 actions with action groups |
| **Complexity** | 4 permit + 4 forbid; three-way job split (internal/distributor/customer) |
| **Synthesis challenge** | Job-based restrictions, customer ID linkage, context-dependent grants |

### 1.5 Streaming Service (`dataset/streaming_service/`)
| Aspect | Detail |
|--------|--------|
| **Cedar features** | `datetime` extension, `duration` extension, `.offset()`, `.toTime()`, subscription tier (`String` comparison), `unless` with temporal logic, nested context |
| **Pattern** | Subscription + temporal ABAC |
| **Schema** | 4 entity types (FreeMember, Subscriber, Movie, Show), 3 actions, Subscription/Profile record types |
| **Complexity** | 6 permit + 1 forbid; 3 datetime-based rules |
| **Synthesis challenge** | Datetime arithmetic, temporal windows, time-of-day modulo, kid profile bedtime |

### 1.6 Tags & Roles (`dataset/tags_n_roles/`)
| Aspect | Detail |
|--------|--------|
| **Cedar features** | Deeply nested optional records, `has` on nested paths, map-like access (`["Role-A"]`), if-then-else chains, `containsAll()`, special `"ALL"` value |
| **Pattern** | Tag-based ABAC with role-scoped tag namespaces |
| **Schema** | 3 entity types (User, Role, Workspace), 3 actions, deeply nested optional record attributes |
| **Complexity** | 2 permit; 6 nested if-then-else blocks per role (3 tags × 2 conditions) |
| **Synthesis challenge** | Deep nesting, optional at every level, "ALL" wildcard semantics, set-subset matching |

### 1.7 Tax Preparer (`dataset/tax_preparer/`)
| Aspect | Detail |
|--------|--------|
| **Cedar features** | Cedar namespaces (`Taxpreparer::`), complex record types (`orgInfo`), `Set.contains()` with record comparison, policy templates (`?principal`, `?resource`), `unless` on forbid, context-passed records |
| **Pattern** | Organization + consent-based ABAC with ad-hoc template overrides |
| **Schema** | 3 entity types (Professional, Document, Client) namespaced, orgInfo/Consent record types, 1 action |
| **Complexity** | 2 permit + 1 forbid; record-in-set matching |
| **Synthesis challenge** | Record-type set membership, consent as runtime context, dual static+template mechanisms |

### 1.8 Clinical Trial (`workspace/`)
| Aspect | Detail |
|--------|--------|
| **Cedar features** | Multi-role membership, numeric comparison (`> 3`, `< 20`), boolean context field, forbid with `unless` exception, string inequality (`!= "HighlyRestricted"`), denormalized attributes |
| **Pattern** | Multi-dimensional RBAC with forbid exception for auditors |
| **Schema** | 4 entity types (User, Role, Project, Document), 2 actions, Long/Bool context |
| **Complexity** | 4 permit + 1 forbid with unless; 6 constraint dimensions |
| **Synthesis challenge** | Forbid/permit with unless, numeric boundary precision, multi-role combinations |

---

## 2. Mutation Operators

These are the reusable building blocks. Each concrete mutation (Section 3) composes 1–5 of these.

### Schema Operators

| ID | Operator | What it does |
|----|----------|-------------|
| S1 | **AddBoolAttribute** | Add a `Bool` attribute to an existing entity type |
| S2 | **AddLongAttribute** | Add a `Long` attribute to an existing entity type |
| S3 | **AddStringAttribute** | Add a `String` attribute to an existing entity type |
| S4 | **AddDatetimeAttribute** | Add a `datetime` attribute to an existing entity type |
| S5 | **AddSetAttribute** | Add a `Set<T>` attribute to an existing entity type |
| S6 | **AddEntityType** | Add a new entity type with attributes and optional parent |
| S7 | **AddAction** | Add a new action with principal/resource/context types |
| S8 | **RemoveAction** | Remove an action from the schema |
| S9 | **AddRole** | Add a new role entity (UserGroup or Role) |
| S10 | **RemoveRole** | Remove a role (redistribute permissions) |
| S11 | **AddContextField** | Add a field to an action's context record |
| S12 | **AddEntityParent** | Add `in [Parent]` to an entity type |
| S13 | **AddRecordType** | Add a named `type` definition |

### Policy Spec Operators

| ID | Operator | What it does |
|----|----------|-------------|
| P1 | **AddForbidRule** | Add a new forbid requirement to the NL spec |
| P2 | **AddPermitRule** | Add a new permit requirement |
| P3 | **RemoveRule** | Remove an existing requirement |
| P4 | **AddUnlessException** | Add an exception to an existing forbid rule |
| P5 | **AddDualPath** | Add an alternative authorization path for an action |
| P6 | **AddSelfPath** | Add entity-equality self-access path (`principal == resource.owner`) |
| P7 | **NarrowCondition** | Tighten an existing condition (e.g., `> 3` → `> 5`) |
| P8 | **BroadenCondition** | Relax an existing condition |
| P9 | **AddTemporalCondition** | Add time-based access restriction |
| P10 | **AddNumericCondition** | Add numeric threshold condition |
| P11 | **AddSetCondition** | Add containsAll/contains requirement |

---

## 3. Concrete Mutation Inventory

### 3.1 GitHub Mutations (13 variants)

#### Easy (5)

| # | ID | Mutation | Operators | Features Tested |
|---|-----|----------|-----------|-----------------|
| 1 | `github_add_private` | Add `isPrivate: Bool` to Repository. Forbid `fork` on private repos. | S1, P1 | boolean_guard, forbid_rule |
| 2 | `github_add_close_issue` | Add `close_issue` action on Issue. Writer+ can close any issue; Reader can close own issue. | S7, P2, P5 | new_action, dual_path |
| 3 | `github_remove_triager` | Remove Triager role; `assign_issue` moves to Writer tier. | S10, P3, P8 | role_redistribution |
| 4 | `github_add_locked_issue` | Add `isLocked: Bool` to Issue. Forbid `edit_issue` on locked issues. | S1, P1 | boolean_guard, forbid_permit_interaction |
| 5 | `github_no_archive` | Remove `isArchived` and the archive forbid rule. Pure RBAC baseline. | S1(remove), P3 | pure_rbac, simplification |

#### Medium (5)

| # | ID | Mutation | Operators | Features Tested |
|---|-----|----------|-----------|-----------------|
| 6 | `github_add_pullrequest` | Add PullRequest entity (attrs: `repo`, `author`). Add `merge_pr` (Writer+), `approve_pr` (Maintainer+). Author cannot approve own PR. | S6, S7×2, P2×2, P1 | new_entity, cross_entity_traversal, self_exclusion |
| 7 | `github_add_contributor` | Add Contributor role between Triager and Writer. Contributors can `push` but not `edit_issue`. | S9, P2, P7 | role_hierarchy, fine_grained_roles |
| 8 | `github_private_and_locked` | Combine: `isPrivate` on Repo (forbid fork) + `isLocked` on Issue (forbid edit). Two independent forbid rules. | S1×2, P1×2 | multi_forbid, boolean_guards |
| 9 | `github_add_visibility` | Replace `isArchived: Bool` with `visibility: String` ("public"/"private"/"internal"). Private blocks fork; internal allows only org members to pull. | S3, P1, P7 | string_enum, multi_value_condition |
| 10 | `github_add_security_admin` | Add `SecurityAdmin` role that can push to archived repos (unless exception on forbid). Keep existing archive rule. | S9, P4 | unless_exception, role_forbid_bypass |

#### Hard (3)

| # | ID | Mutation | Operators | Features Tested |
|---|-----|----------|-----------|-----------------|
| 11 | `github_pr_review_workflow` | Add PullRequest + Review entities. merge_pr requires at least one approved Review. Author can't approve own PR. Forbid merge on archived repos. | S6×2, S7×3, P2×3, P1×2 | multi_entity, cross_traversal, self_exclusion, forbid |
| 12 | `github_full_expansion` | Add: PullRequest entity, `isPrivate` bool, `isLocked` bool, Contributor role, `close_issue` action. 5 simultaneous mutations. | S6, S1×2, S9, S7, P2×2, P1×2 | multi_mutation, complexity |
| 13 | `github_numeric_constraints` | Add `maxCollaborators: Long` to Repo, `accountAge: Long` to User. Forbid adding roles if at capacity. Forbid push if account age < 30. | S2×2, P1×2, P10 | numeric_comparison, multi_constraint |

### 3.2 Document Cloud Mutations (9 variants)

#### Easy (3)

| # | ID | Mutation | Operators | Features Tested |
|---|-----|----------|-----------|-----------------|
| 14 | `doccloud_remove_blocking` | Remove the `blocked` attribute and blocking forbid rules. Simpler model. | S5(remove), P3 | simplification |
| 15 | `doccloud_add_comment_acl` | Add `commentACL: DocumentShare` to Document. Add `CommentOnDocument` action. Commenters can view + comment. | S5, S7, P2 | new_acl_tier, action_addition |
| 16 | `doccloud_remove_public` | Remove Public entity and public access rules. Only authenticated users. | P3, S6(remove) | simplification, auth_only |

#### Medium (4)

| # | ID | Mutation | Operators | Features Tested |
|---|-----|----------|-----------|-----------------|
| 17 | `doccloud_add_expiry` | Add `expiryDate: datetime` to Document. Forbid all access after expiry. Owner can still delete expired docs. | S4, P1, P4 | datetime, forbid_with_unless |
| 18 | `doccloud_add_version_lock` | Add `isLocked: Bool` to Document. Forbid `ModifyDocument` on locked docs. Owner can still delete. | S1, P1, P4 | boolean_guard, owner_exception |
| 19 | `doccloud_add_admin_group` | Add `manageACL` grants admin privileges that bypass blocking. Admin can view/modify even if blocked. | P4, P2 | unless_exception, role_bypass |
| 20 | `doccloud_graduated_sharing` | Change `publicAccess` semantics: add "preview" level (view metadata only, not content). Three-tier: none/preview/view/edit. | P7, P2 | string_enum, multi_value |

#### Hard (2)

| # | ID | Mutation | Operators | Features Tested |
|---|-----|----------|-----------|-----------------|
| 21 | `doccloud_temporal_sharing` | Add `shareExpiry: datetime` to Document. Sharing links (ACL access) expire but owner access persists. Plus version lock. | S4, S1, P1, P9, P4 | datetime, boolean_guard, owner_exception |
| 22 | `doccloud_org_isolation` | Add Organization entity. Users belong to Orgs. Forbid cross-org document access. Admins (manageACL) can share cross-org. | S6, S12, P1, P4 | entity_hierarchy, org_isolation, unless_exception |

### 3.3 Streaming Service Mutations (9 variants)

#### Easy (3)

| # | ID | Mutation | Operators | Features Tested |
|---|-----|----------|-----------|-----------------|
| 23 | `streaming_remove_bedtime` | Remove kid bedtime restriction. Simpler temporal rules. | P3 | simplification |
| 24 | `streaming_add_download` | Add `download` action (Subscriber only, no free content download). | S7, P2, P1 | new_action, principal_type_check |
| 25 | `streaming_remove_oscars` | Remove Oscar promo window. Focus on early access + bedtime only. | P3 | simplification |

#### Medium (3)

| # | ID | Mutation | Operators | Features Tested |
|---|-----|----------|-----------|-----------------|
| 26 | `streaming_add_geo_restriction` | Add `region: String` to context, `allowedRegions: Set<String>` to Movie/Show. Forbid watch if region not in allowedRegions. | S11, S5, P1, P11 | context_field, set_containment |
| 27 | `streaming_add_trial_tier` | Add `TrialMember` entity with `trialExpiry: datetime`. Can watch free content + limited non-free until trial expires. | S6, P2, P9 | new_entity_type, temporal_constraint |
| 28 | `streaming_add_age_rating` | Add `rating: String` to Movie/Show ("G"/"PG"/"PG13"/"R"). Kid profiles can only watch G/PG. | S3, P1 | string_enum, profile_restriction |

#### Hard (3)

| # | ID | Mutation | Operators | Features Tested |
|---|-----|----------|-----------|-----------------|
| 29 | `streaming_parental_controls` | Add age rating + `maxRating: String` on Profile. Forbid content above profile's max rating. Plus bedtime. Two forbid rules. | S3×2, P1×2 | multi_forbid, string_comparison, profile_attrs |
| 30 | `streaming_multidevice` | Add `activeStreams: Long` to context. Standard subscribers limited to 2 concurrent; premium to 5. Forbid if over limit. | S11, P1, P10 | numeric_context, tier_differentiation |
| 31 | `streaming_full_expansion` | Add download + geo-restriction + age rating. Three new constraints simultaneously. | S7, S11, S5, S3, P2, P1×3 | multi_mutation, complexity |

### 3.4 Clinical Trial Mutations (10 variants)

#### Easy (3)

| # | ID | Mutation | Operators | Features Tested |
|---|-----|----------|-----------|-----------------|
| 32 | `clinical_remove_auditor` | Remove GlobalAuditor loophole. Strict department matching, no exceptions. | P3, P7 | simplification, strict_forbid |
| 33 | `clinical_add_export` | Add `Export` action with same constraints as View but also requires `isCompliantDevice`. All roles need compliant device to export. | S7, P2 | new_action, uniform_constraint |
| 34 | `clinical_relax_clearance` | Change `clearanceLevel > 3` to `>= 3`. Tests numeric boundary precision. | P8 | boundary_precision |

#### Medium (4)

| # | ID | Mutation | Operators | Features Tested |
|---|-----|----------|-----------|-----------------|
| 35 | `clinical_add_datamanager` | Add `DataManager` role. DataManagers can Edit `HighlyRestricted` docs if `clearanceLevel > 5`. New dual-path for Edit. | S9, P2, P5 | new_role, dual_path, higher_threshold |
| 36 | `clinical_add_study_phase` | Add `studyPhase: String` to Document. Phase-3 docs restricted to PrincipalInvestigator only (ClinicalResearcher blocked). | S3, P1 | string_condition, role_restriction |
| 37 | `clinical_add_consent` | Add `hasPatientConsent: Bool` to context. Forbid Edit without consent. View still allowed. Action-specific forbid. | S11, P1 | context_bool, action_specific_forbid |
| 38 | `clinical_dual_forbid` | Add second forbid: forbid access to HighlyRestricted docs from non-compliant devices. Auditor exempt from department block but NOT from device check. | P1 | multi_forbid, selective_bypass |

#### Hard (3)

| # | ID | Mutation | Operators | Features Tested |
|---|-----|----------|-----------|-----------------|
| 39 | `clinical_add_sponsor` | Add Sponsor entity + SponsorRepresentative role. Sponsors can View (not Edit) cross-department docs only for Active Phase-3 projects. Third role path. | S6, S9, P2 | new_entity, new_role, triple_path |
| 40 | `clinical_temporal_embargo` | Add `embargoUntil: datetime` to Document, `requestTime: datetime` to context. Forbid access before embargo except PrincipalInvestigator. | S4, S11, P1, P4 | datetime, forbid_unless, temporal |
| 41 | `clinical_full_expansion` | DataManager + study phase + consent + second device forbid. Four simultaneous constraints. | S9, S3, S11, P2, P1×3 | multi_mutation, complexity |

### 3.5 Hotel Chains Mutations (8 variants)

#### Easy (3)

| # | ID | Mutation | Operators | Features Tested |
|---|-----|----------|-----------|-----------------|
| 42 | `hotel_add_guest` | Add Guest role: view-only on Reservations under their name. No Property/Hotel access. | S9, P2, P6 | new_role, self_path, restricted_scope |
| 43 | `hotel_add_cancel` | Add `cancelReservation` action. Member+ can cancel. Viewer cannot. | S7, P2 | new_action, role_threshold |
| 44 | `hotel_remove_hierarchy` | Flatten Property/Hotel: remove `Property in [Hotel]`. All permissions must be explicit (no inheritance). | S12(remove), P7 | flat_model, no_inheritance |

#### Medium (3)

| # | ID | Mutation | Operators | Features Tested |
|---|-----|----------|-----------|-----------------|
| 45 | `hotel_add_renovation_lock` | Add `isUnderRenovation: Bool` on Property. Forbid `createReservation` on renovating properties. Admin can override. | S1, P1, P4 | boolean_guard, unless_exception |
| 46 | `hotel_add_franchise` | Add Franchise entity above Hotel (`Hotel in [Franchise]`). Franchise admin inherits hotel admin. 4-level hierarchy. | S6, S12, P2 | deep_hierarchy, inheritance |
| 47 | `hotel_add_loyalty_tier` | Add `loyaltyTier: Long` to User. Premium properties require `loyaltyTier >= 3` for reservation. | S2, P10 | numeric_constraint, resource_restriction |

#### Hard (2)

| # | ID | Mutation | Operators | Features Tested |
|---|-----|----------|-----------|-----------------|
| 48 | `hotel_franchise_loyalty` | Franchise hierarchy + loyalty tier + renovation lock. Three interacting constraints. | S6, S12, S2, S1, P2, P10, P1, P4 | deep_hierarchy, numeric, boolean_guard |
| 49 | `hotel_temporal_rates` | Add `seasonStart: datetime`, `seasonEnd: datetime` to Property. Rate viewing restricted to active season. Reservation viewable anytime. | S4×2, S11, P9 | datetime, action_scoped_temporal |

### 3.6 Tags & Roles Mutations (7 variants)

#### Easy (2)

| # | ID | Mutation | Operators | Features Tested |
|---|-----|----------|-----------|-----------------|
| 50 | `tags_add_role_c` | Add Role-C with its own tag set and a new `ArchiveWorkspace` action. | S9, S7, P2 | role_addition, nested_record_extension |
| 51 | `tags_remove_all_wildcard` | Remove "ALL" special-value semantics. Strict tag matching only. | P7 | strict_matching, simplification |

#### Medium (3)

| # | ID | Mutation | Operators | Features Tested |
|---|-----|----------|-----------|-----------------|
| 52 | `tags_add_sensitivity` | Add `sensitivity: Long` to Workspace. Role-A can access sensitivity <= 3; Role-B <= 1. | S2, P10 | numeric_constraint, role_differentiation |
| 53 | `tags_add_owner_bypass` | Add `owner: User` to Workspace. Owner can always ReadWorkspace regardless of tags. | S5, P6 | owner_path, dual_path |
| 54 | `tags_add_approval` | Add `isApproved: Bool` to Workspace. Unapproved workspaces: ReadWorkspace only (no Update/Delete even for Role-A). | S1, P1 | boolean_guard, action_restriction |

#### Hard (2)

| # | ID | Mutation | Operators | Features Tested |
|---|-----|----------|-----------|-----------------|
| 55 | `tags_add_fourth_dimension` | Add `department` tag group (4th dimension). Extends the nested record with another optional level. | S5, P11 | deep_nesting, containsAll_extension |
| 56 | `tags_sensitivity_and_owner` | Sensitivity levels + owner bypass + approval status. Three layered constraints on top of tag matching. | S2, S5, S1, P10, P6, P1 | multi_constraint, complexity |

### 3.7 Tax Preparer Mutations (7 variants)

#### Easy (2)

| # | ID | Mutation | Operators | Features Tested |
|---|-----|----------|-----------|-----------------|
| 57 | `tax_remove_consent` | Remove consent forbid rule. Org-matched professionals can always access. | P3 | simplification |
| 58 | `tax_add_edit` | Add `editDocument` action. Same org-matching required. Consent still applies. | S7, P2 | new_action |

#### Medium (3)

| # | ID | Mutation | Operators | Features Tested |
|---|-----|----------|-----------|-----------------|
| 59 | `tax_add_supervisor` | Add Supervisor role. Supervisors can `viewDocument` for any document in their organization (no serviceline/location matching). | S9, P2, P8 | role_bypass, broadened_access |
| 60 | `tax_add_sensitivity` | Add `isSensitive: Bool` to Document. Sensitive docs require `team_region_list` to include `"HQ"` (additional consent constraint). | S1, P7 | boolean_guard, set_containment |
| 61 | `tax_add_client_profile` | Add `viewClientProfile` action on Client entity. Org matching applies. | S7, P2 | multi_resource_type |

#### Hard (2)

| # | ID | Mutation | Operators | Features Tested |
|---|-----|----------|-----------|-----------------|
| 62 | `tax_add_auditor` | Add Auditor role + `auditDocument` action. Auditors bypass org matching but still need consent. | S9, S7, P2, P4 | role_bypass, unless_exception |
| 63 | `tax_full_expansion` | Supervisor + sensitivity + edit + auditor. Four simultaneous additions. | S9×2, S7×2, S1, P2×4, P4 | multi_mutation, complexity |

### 3.8 Sales Orgs Mutations (8 variants)

#### Easy (3)

| # | ID | Mutation | Operators | Features Tested |
|---|-----|----------|-----------|-----------------|
| 64 | `sales_remove_customer_restriction` | Remove forbid on customer-to-customer sharing. Anyone can share with anyone. | P3 | simplification |
| 65 | `sales_add_archive` | Add `isArchived: Bool` to Presentation. Forbid edit on archived presentations. Owner can still view. | S1, P1 | boolean_guard |
| 66 | `sales_add_delete` | Add `deletePresentation` action. Only owner can delete. | S7, P2 | new_action, owner_only |

#### Medium (3)

| # | ID | Mutation | Operators | Features Tested |
|---|-----|----------|-----------|-----------------|
| 67 | `sales_add_regional_manager` | Add `RegionalManager` job type. Regional managers can edit templates across all markets (bypass market membership). | S9, P2, P4 | job_addition, market_bypass |
| 68 | `sales_add_approval` | Add `isApproved: Bool` to Template. Unapproved templates: view-only for non-internal users. Internal can still edit. | S1, P1 | boolean_guard, job_conditional |
| 69 | `sales_add_team` | Add Team entity. Users belong to Teams. Presentations shared with Teams (Set<Team> attribute). | S6, S5, P2 | new_entity, team_sharing |

#### Hard (2)

| # | ID | Mutation | Operators | Features Tested |
|---|-----|----------|-----------|-----------------|
| 70 | `sales_temporal_campaign` | Add `campaignStart: datetime`, `campaignEnd: datetime` on Presentation. Non-internal users can only view during campaign window. | S4×2, S11, P9 | datetime, job_conditional_temporal |
| 71 | `sales_full_expansion` | Regional manager + approval + archive + delete. Four additions. | S9, S1×2, S7, P2×2, P1×2 | multi_mutation, complexity |

---

## 4. Feature Coverage Matrix

Each column is a Cedar feature / synthesis challenge. Each row is a scenario. ✓ = already present in base, **M** = added by a mutation.

| Feature | GitHub | DocCloud | Streaming | Clinical | Hotel | Tags | Tax | Sales |
|---------|--------|----------|-----------|----------|-------|------|-----|-------|
| Entity group membership | ✓ | ✓ | | | ✓ | ✓ | | |
| Cross-entity traversal | ✓ | | | | ✓ | | ✓ | |
| Entity equality (self-path) | ✓ | ✓ | | | **M42** | **M53** | | |
| Boolean guard + forbid | ✓ | | | | **M45** | **M54** | **M60** | **M65** |
| Forbid/permit interaction | ✓ | ✓ | ✓ | ✓ | **M45** | | ✓ | ✓ |
| Unless exception on forbid | **M10** | **M19** | | ✓ | **M45** | | **M62** | |
| Dual-path authorization | ✓ | ✓ | | **M35** | | **M53** | | |
| Numeric constraints | **M13** | | **M30** | ✓ | **M47** | **M52** | | |
| Datetime operations | | **M17** | ✓ | **M40** | **M49** | | | **M70** |
| String enum conditions | **M9** | ✓ | | | | | | |
| Set containment (containsAll) | | ✓ | **M26** | | ✓ | ✓ | ✓ | |
| Optional / `has` checks | | ✓ | | | | ✓ | | |
| Nested record attributes | | | | | ✓ | ✓ | ✓ | |
| Policy templates | | | | | base(templated) | | ✓ | base(templated) |
| Context fields | | ✓ | ✓ | ✓ | | | ✓ | ✓ |
| Public principal type | | ✓ | | | | | | |
| Action groups | | | | | | ✓ | | ✓ |
| Cedar namespaces | | | | | | | ✓ | |
| Hierarchical inheritance | | | | | ✓ | | | |
| Multi-role membership | | | | ✓ | | ✓ | | |
| `is` type check | | | ✓ | | ✓ | | | |

---

## 5. Difficulty Distribution

| Tier | Count | Criteria |
|------|-------|----------|
| **Easy** | 24 | 1 schema change + 1 spec change. Single new concept. |
| **Medium** | 28 | 2–3 coordinated changes. Tests feature interactions. |
| **Hard** | 19 | 3–5 changes. Multiple interacting features. |
| **Total mutations** | **71** | |
| **Base scenarios** | **8** | (Included as-is for baseline measurement) |
| **Grand total** | **79** | |

---

## 6. Implementation Architecture

### 6.1 Generator Output

For each scenario, the generator produces a directory:

```
cedarbench/
├── manifest.json                    # Metadata for all scenarios
├── github_base/
│   ├── schema.cedarschema
│   └── policy_spec.md
├── github_add_private/
│   ├── schema.cedarschema
│   └── policy_spec.md
├── github_add_close_issue/
│   ├── schema.cedarschema
│   └── policy_spec.md
├── ...
├── clinical_base/
├── clinical_add_datamanager/
├── ...
└── sales_full_expansion/
```

Each scenario contains ONLY:
- `schema.cedarschema` — Valid Cedar schema (mutated from base)
- `policy_spec.md` — Coherent NL policy specification (reflecting mutation)

Phase 1 of the eval harness generates verification plans and references. Phase 2 does synthesis.

### 6.2 Generator Design

```
cedarbench/
├── generate.py              # Main entry point
├── base_scenarios.py        # Registry of base scenario paths + loaders
├── schema_ops.py            # Cedar schema string manipulation helpers
├── mutations/
│   ├── github.py            # GitHub domain mutations
│   ├── doccloud.py          # Document Cloud mutations
│   ├── streaming.py         # Streaming Service mutations
│   ├── clinical.py          # Clinical Trial mutations
│   ├── hotel.py             # Hotel Chains mutations
│   ├── tags.py              # Tags & Roles mutations
│   ├── tax.py               # Tax Preparer mutations
│   └── sales.py             # Sales Orgs mutations
└── scenarios/               # Generated output (gitignored)
```

### 6.3 Schema Manipulation Strategy

Cedar schema files are structured text. The generator uses **targeted string operations** (not a full parser) to apply schema mutations:

1. **`add_attribute(schema, entity_name, attr_name, attr_type)`** — Inserts before the closing `};` of the entity block
2. **`remove_attribute(schema, entity_name, attr_name)`** — Removes the attribute line
3. **`add_entity(schema, entity_def)`** — Appends a new entity declaration
4. **`add_action(schema, action_def)`** — Appends a new action declaration
5. **`add_type(schema, type_def)`** — Prepends a type definition
6. **`modify_entity_parents(schema, entity_name, parents)`** — Changes `in [...]` clause

### 6.4 Spec Generation Strategy

Each mutation defines its NL spec as a **full replacement** of the base spec's relevant sections. This avoids fragile text patching:

1. Load the base `policy_spec.md`
2. The mutation provides:
   - `context_additions` — Extra context paragraphs (entity model changes)
   - `requirement_additions` — New numbered requirements to append
   - `requirement_modifications` — Dict mapping requirement number to replacement text
   - `requirement_removals` — Set of requirement numbers to remove
   - `notes_additions` — Extra notes
3. The generator assembles the final spec from these components

### 6.5 Manifest Schema

```json
{
  "version": "1.0",
  "generated": "2026-04-04",
  "scenarios": [
    {
      "id": "github_add_private",
      "domain": "github",
      "base_scenario": "github_base",
      "difficulty": "easy",
      "mutation_description": "Add isPrivate boolean to Repository; forbid fork on private repos",
      "operators_applied": ["S1", "P1"],
      "features_tested": ["boolean_guard", "forbid_rule"],
      "path": "scenarios/github_add_private/"
    }
  ]
}
```

---

## 7. Validation Criteria

Each generated scenario must satisfy:

1. **Schema validity**: The `.cedarschema` file must parse without errors (testable via `cedar validate`)
2. **Spec coherence**: The `policy_spec.md` must describe a policy that is realizable given the schema — every entity, attribute, and action referenced in the spec must exist in the schema
3. **Non-triviality**: The mutation must produce a meaningfully different synthesis challenge (not just a rename)
4. **Feature coverage**: The mutation must exercise at least one Cedar feature not already tested by the base scenario
5. **Consistency**: Schema entity/attribute names in the spec must match the schema exactly
