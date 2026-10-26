---
name: autocedar
description: Turn natural-language access-control requirements into a Cedar policy that is verified against a human-reviewed target, or verify an existing Cedar policy against its verification plan. Use when the user wants Cedar authorization policies written from requirements, prose, tickets or regulations, asks to check a Cedar policy with cedar symcc, or mentions AutoCedar, floors, ceilings or liveness slices.
---

# AutoCedar

AutoCedar splits requirements into small **intent atoms**. Schema atoms fix the vocabulary (entities, attributes, actions). Property atoms state behavior: a **floor** lists requests that must be allowed, a **ceiling** bounds what may be allowed, and a **liveness slice** is a class of requests that must not be emptied. The user approves each atom. AutoCedar then compiles the approved atoms into a verification target and synthesizes a Cedar policy that `cedar symcc` proves satisfies it.

The `autocedar` MCP server provides the tools named below.

## The one rule

**The user decides every atom.** AutoCedar's guarantee is only as good as the approved target, and that target is the user's judgment, not yours.

- Show each pending atom to the user and wait for their answer.
- Never approve, reject or edit an atom on your own, even when it looks obviously right.
- Never set `confirm_failed_checks` unless the user approved an atom after you told them which checks failed.

You may explain an atom, point out where it seems to differ from the requirements, or answer questions about it. The decision stays theirs.

## 1. Check the setup

Call `doctor`. If a check fails, show its `fix` to the user:

- **Cedar CLI or CVC5 missing:** ask before running `autocedar setup --yes`, because it installs software.
- **Model provider not signed in:** AutoCedar proposes atoms with its own model provider. Inside Claude Code, pass `provider: "claude-cli"` to use the user's Claude Code login. Inside Codex, pass `provider: "codex"`.

If the `autocedar` tools are missing altogether, the MCP server did not start. It runs through `uvx`, so check that `uv` is installed (`uv --version`), or install AutoCedar with `uv tool install autocedar`.

## 2. Author a policy from requirements

1. Get the requirements as a file. If the user pasted text, ask where to save it, then write it.
2. Call `author_start` with absolute paths: `spec_path`, and an `out_dir` for the session. Pass `schema_path` if the user already has a Cedar schema.
3. Loop on the returned `state`:
   - **`awaiting_review`.** Present `pending_review` to the user:
     - `stage` and position (`index` of `total`);
     - `kind` and, for property atoms, `constraint_type`;
     - the `summary`, which is the claim being approved;
     - the `source_excerpt` it came from;
     - the `cedar` encoding;
     - any `symbolic_checks` that failed.

     Ask them to approve, reject with a reason, or edit (`field=value`, e.g. `plain_english_summary=...` or `reference_cedar=...`). Send their answer with `author_review`, passing the same `request_id`.
     - An edit returns the edited atom; show it again before asking.
     - A rejected property atom goes to AutoCedar's repair planner, which may propose a replacement for review.
   - **`running`.** The pipeline is proposing atoms or synthesizing. Call `author_status`, which waits. Tell the user briefly what `recent_events` shows.
   - **`finished`.**
     - If `result.completed` is true, show the Cedar policy (`candidate_cedar`) and the session directory.
     - If it is false, show the `notes`: construction stopped, for example on a floor and ceiling that conflict, and the user has to resolve it.
   - **`error`.** Show the error. A run can be continued with `author_start` and `resume_session` set to the session directory.
   - **`paused`.** The run was paused with `author_pause`. Resume it the same way.

Describe the result accurately. The policy is verified against the target the user approved. It is not proven against the prose itself.

## 3. Verify an existing policy

For a workspace directory that holds `schema.cedarschema`, `candidate.cedar` and `verification_plan.py`, call `verify` with its absolute path.

- Report each failed check with its counterexample.
- A failed ceiling means the policy allows too much. A failed floor means it denies a required request. A failed liveness check means a required workflow is blocked.
