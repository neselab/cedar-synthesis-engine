# CyberChair Manual AITL Trace

This trace simulates the intended AutoCedar workflow for the CyberChair prose
while bypassing the currently broken Stage 1 schema-packet behavior. Codex acted
as the reviewing oracle and manually compared each modeling decision against the
provided requirements.

## Source

Input spec:

- `experiments/rede_autocedar/cyberchair_human/spec.md`

Manual AITL workspace:

- `experiments/rede_autocedar/cyberchair_manual_aitl/`

## Procedure

1. Read the CyberChair prose as the human reviewer.
2. Separated authorization intent from non-authorization workflow details.
3. Built a schema with explicit lifecycle/status hooks needed by the policy
   atoms.
4. Wrote reviewed floor/ceiling/liveness targets as Cedar references.
5. Wrote a candidate Cedar policy store.
6. Validated the schema, candidate, and every reference with `cedar validate`.
7. Ran AutoCedar verification with `uv run autocedar verify`.

## Stage 1: Reviewed Schema Decisions

Approved principal model:

- `User.role: String`
  - Accepted as a compact representation of author, reviewer, chair, and PCC.
  - This is acceptable for this trace because the prose describes role-based
    access but does not require role intersection behavior.
- `User.submittedAllAssignedReviews: Bool`
  - Needed for the "reviewer has submitted all his reviews and has time to
    review more papers" condition.

Approved resources:

- `Submission`
  - Represents an abstract/paper submission.
  - Carries authors, contact person, assigned reviewers, conflicted reviewers,
    reviewers who have submitted, lifecycle flags, selection state, and review
    quality flags.
- `ReviewerDirectory`
  - Represents the personal webserver directory for one reviewer.
- `ReviewFile`
  - Represents files written into reviewer directories, including forms and
    other reviewers' reviews.
- `ReviewOverview`
  - Represents chair/PCC monitoring views over papers/reviews.

Approved lifecycle/context hooks:

- `Submission.step1Open`
- `Submission.step2Open`
- `Submission.reviewOpen`
- `Submission.reviewProcessDone`
- `Submission.distributionDone`
- `Submission.selected`
- `Submission.hasConflictingReviews`
- `Submission.onlyNonExpertReviews`
- `context.hasStep2Credential`
- `context.expertiseLevel`
- `context.willingness`

Rejected / not modeled as schema intent:

- Unique submission id assignment.
- Sending login/password emails.
- Physical copying of files into directories.
- The literal generated hyperlink objects.

Reason: these are workflow/infrastructure facts, not authorization decisions in
the policy store.

## Stage 2: Reviewed Property Target

The approved target uses ceilings to bound excess access and selected floors to
force required workflows. Each non-liveness reference was validated against the
schema.

Ceilings:

1. `submit_step1_ceiling`
   - Only authors of the submission may submit step-1 material while step 1 is
     open.
2. `submit_full_paper_ceiling`
   - Only authors with step-2 credentials may upload full papers during step 2.
3. `update_step1_ceiling`
   - Only authors with step-2 credentials may correct step-1 information during
     step 2.
4. `camera_ready_ceiling`
   - Only authors of selected submissions may submit camera-ready versions after
     review.
5. `download_assigned_ceiling`
   - Only assigned, non-conflicted reviewers may download papers after
     distribution.
6. `display_abstract_ceiling`
   - Same boundary as paper download for abstract display.
7. `submit_review_ceiling`
   - Only assigned, non-conflicted reviewers may submit reviews while review is
     open.
8. `update_review_ceiling`
   - Same boundary as submit review.
9. `read_other_reviews_ceiling`
   - Reviewers may read other reviews only after submitting their own review for
     the paper.
10. `volunteer_conflicting_paper_ceiling`
    - Reviewers may volunteer for papers with conflicting reviews only after
      finishing assigned reviews and when they are not conflicted with the
      paper.
11. `monitor_ceiling`
    - Only chair/PCC roles may monitor review overviews.
12. `ask_additional_reviewer_ceiling`
    - Only PCC may ask additional reviewers for low-expertise papers.
13. `directory_access_ceiling`
    - Reviewer directories are protected by owner or allowed-user list.
14. `review_file_access_ceiling`
    - Review files are protected by the file and directory allowed-user lists.

Floors:

1. `author_submit_step1_floor`
   - Authors must be able to submit step-1 material during step 1.
2. `reviewer_read_other_reviews_floor`
   - Reviewers who submitted their own review must be able to read other
     reviews for that paper.
3. `pcc_ask_additional_reviewer_floor`
   - PCC must be able to request extra review on low-expertise papers.

Liveness:

1. `liveness_submit_step1`
2. `liveness_submit_review`
3. `liveness_monitor`

Note: AutoCedar's current liveness check is broad `not always-denies` for an
action/resource/principal type. The floors above provide more targeted
existential coverage for the important workflows, but AutoCedar should upgrade
liveness to use explicit probe overlap checks.

## Stage 3: Candidate Policy

Candidate:

- `candidate.cedar`

The policy is intentionally compact and uses one permit branch per approved
workflow group. It does not include broad unconditional role grants.

## Verification Commands

Schema/candidate validation:

```bash
cedar validate \
  --schema experiments/rede_autocedar/cyberchair_manual_aitl/schema.cedarschema \
  --policies experiments/rede_autocedar/cyberchair_manual_aitl/candidate.cedar
```

Reference validation:

```bash
for f in experiments/rede_autocedar/cyberchair_manual_aitl/references/*.cedar; do
  cedar validate \
    --schema experiments/rede_autocedar/cyberchair_manual_aitl/schema.cedarschema \
    --policies "$f"
done
```

Full target verification:

```bash
uv run autocedar verify experiments/rede_autocedar/cyberchair_manual_aitl
```

Result:

```text
loss: 0
```

All 20 checks passed:

- 14 ceilings
- 3 floors
- 3 liveness checks

## Issues Encountered

1. Stage 1 source packetization is still wrong for large single-section specs.
   - Diagnostic run: `cyberchair-diagnostic-10s`
   - AutoCedar produced one schema packet with 20 focus nodes and 5 related
     nodes.
   - The first schema LLM call took roughly 2.5 minutes and returned only one
     schema atom, `ExpertiseLevel`.
   - Fix needed: Stage 1 should propose schema deltas per source node or small
     bounded packet, not per section.

2. Stage 1 prompt is still too global.
   - Current behavior asks for "schema atoms for the spec above."
   - Correct behavior: "Given this current source node plus local context and
     the current approved schema, propose only missing schema delta atoms or
     report already-covered."

3. Liveness is too broad in the verification plan type.
   - Current `always-denies-liveness` asks whether the candidate denies every
     request for an action/resource/principal type.
   - Better liveness: compile a liveness probe reference and check that the
     candidate is not disjoint from that probe.

4. CyberChair prose contains workflow facts mixed with authorization facts.
   - The schema/policy should not model every system behavior.
   - AutoCedar needs a first-class "not authorization intent" decision type in
     both Stage 1 and Stage 2 coverage ledgers.

5. Role representation is a real modeling choice.
   - I used `User.role: String` for a compact trace.
   - A stronger production model may use separate entity types for Author,
     Reviewer, Chair, and PCC if role intersection matters.
   - AutoCedar should surface this as a schema-review choice, not silently pick
     one representation.

6. Reviewer expertise and willingness are bounded string domains.
   - The schema uses context strings and policy checks allowed values.
   - A better Cedar schema could model these as enum entities or type aliases if
     the rest of the system needs reusable domain values.

7. The manual workflow was faster and cleaner than the current CLI path because
   I did schema/property decomposition directly.
   - This confirms that the bottleneck is not the model's raw capability.
   - The bottleneck is AutoCedar's current decomposition/control surface.

