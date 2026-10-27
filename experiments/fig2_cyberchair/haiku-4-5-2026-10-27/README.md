# Fig. 2: CyberChair through the intent-map pipeline

**Question.** What does the intent-map pipeline produce for requirement R7 of
CedarBench's CyberChair scenario, and how does synthesis repair its first
failed candidate? This run supplies Fig. 2 of the paper.

## Configuration

- Input: `cedarbench/scenarios/realworld/ultra_cyberchair/policy_spec.md` and
  `schema.cedarschema`, copied to `input/`. The schema is fixed (`--schema`,
  `--max-schema-gap-repairs 0`).
- Model: Claude Haiku 4.5 (`claude-haiku-4-5`) through the `claude-cli`
  provider, effort `high`.
- Review: `--model-review`. No person reviewed the atoms, so the result does
  not count as human approval (`approved: False` in `console.log`).
- Code: commit `2b5467ec` plus the two fixes later committed in `d726bc78`
  (`RUN.json` lists the files that were uncommitted at run time).
- Command: `run.sh`. It points at the worktree used for the run; set `WT` to
  your checkout.

## Result

- Intent map: 14 scopes, one per action the spec mentions, all marked
  complete. Approved in round 2: the model reviewer rejected round 1 for
  deny-all scopes on three actions the spec never mentions
  (`stage0/intent_map.json`).
- 14 condition atoms approved, none rejected (`stage2/approved_atoms.json`).
- Floors and ceilings calculated from the map (`stage2/derived_boundaries.json`).
- Synthesis converged in 2 iterations; all 42 checks pass. The first candidate
  failed the ceilings for R9 (`volunteerForConflictingPaper`) and R11
  (`askAdditionalReviewer`) (`harness_runs/scenario/iterations/`).

Fig. 2 uses R7's map entry, condition atom, and floor (= ceiling), and R9's
first candidate, counterexample, and repair (`iter_1/feedback.md`,
`iter_2/candidate.cedar`).

## Limits

- R9's condition atom leaves out "papers with conflicting reviews"
  (`resource.hasConflictingReviews`), and model review approved it.
- R7's atom states only what R7 says: it does not require that the reader is
  assigned to the paper or not conflicted with it.
- The run predates the permission-list question (`d726bc78`); here the map
  marked every scope complete on its own.

## Earlier attempts

Four earlier attempts with the same configuration stopped on bugs that
`d726bc78` fixes: the Claude CLI ended structured calls with `error_max_turns`
(attempts 1, 3, 4), and the schema-support check reported a false schema gap
for `entity E = { ... }` (attempt 2). Their outputs are not committed.
