# AutoCedar Research Integrity Constitution

This document is a binding working rule for AutoCedar development and
experiments. AutoCedar's core claim is that access-control intent can be
decomposed, reviewed, formalized, and checked by general mechanisms. Any hidden
shortcut that makes a known scenario pass damages that claim.

## Prime Directive

Do not make AutoCedar look smarter than it is.

If a behavior depends on knowing the answer to a specific scenario, it is not a
general AutoCedar capability. It must not be added to the live pipeline, signal
layer, prompts, tests, or evaluation path unless it is explicitly labeled as a
scenario-specific ablation or debugging artifact and excluded from claimed
results.

## Non-Negotiable Rules

1. No answer-sheet logic.
   AutoCedar must not contain repair rules keyed to domain nouns such as
   particular roles, resources, datasets, scenarios, or benchmark examples.

2. No hidden semantic shortcuts.
   If a human or external agent supplies semantic judgment, record it as HITL or
   AITL judgment. Do not encode that judgment as if AutoCedar discovered it
   through its verifier loop.

3. Isomorphism test.
   Before adding any signal-layer rule, ask whether it still works if every
   domain noun is renamed. If the answer is no, it does not belong in the
   general signal layer.

4. Verifier-grounded feedback only.
   Signal-layer feedback may reshape evidence from Cedar validation, SymCC/CVC5,
   candidate/reference comparison, check identity, source provenance, and
   convergence history. It may not invent policy intent.

5. Structural signals are allowed; vocabulary signals are not.
   Allowed: candidate/reference diff, missing same-action branch, extra guard,
   different session binding field, type mismatch, optional-attribute safety
   error, repeated oscillation.
   Not allowed: "if this scenario mentions personal representatives, suggest
   this exact repair."

6. Preserve the division of labor.
   The LLM proposes and reasons. The human or reviewing agent judges intent.
   Cedar validation checks syntax and type safety. SymCC/CVC5 checks semantic
   containment/liveness/disjointness. The signal layer packages feedback; it
   does not become an oracle.

7. Never optimize the benchmark at the expense of the claim.
   A worse-looking honest failure is better than a cleaner-looking contaminated
   pass.

8. Manual HITL simulation must stay manual.
   When Codex simulates the human reviewer, it must inspect each atom against
   the requirements and Cedar semantics. It must not use scripted name matching
   or hidden aliases as semantic approval.

9. Saved artifacts must be clean artifacts.
   Persist only approved atom states, valid references, final schemas, final
   policies, transcripts, verifier outputs, and clearly marked diagnostics. Do
   not replay stale or invalid intermediate data as if it had passed review.

10. Report failures plainly.
    If a run fails because of schema gaps, invalid references, missing verifier
    setup, model timeout, or bad prompting, say that directly. Do not reframe it
    as policy convergence.

11. Ask before improvising around setbacks.
    When a setback threatens the validity of the experiment, stop and ask the
    user how to proceed. Do not silently add shortcuts, broaden assumptions,
    relax checks, patch around the failure, or encode scenario knowledge to get
    past the obstacle.

## Acceptable Signal Layer

The signal layer may include:

- raw Cedar validator output;
- raw SymCC/CVC5 result and witness when available;
- check name, check type, and floor/ceiling/liveness/disjointness direction;
- source atom provenance;
- reference policy excerpt;
- candidate policy excerpt for the same action;
- candidate/reference diff;
- generic structural deltas, such as missing guard, extra guard, branch mismatch,
  different session binding, or action/resource mismatch;
- convergence history, repeated failure classes, and oscillation detection;
- verifier setup classification, such as missing CVC5 or unavailable SymCC
  analysis support.

The signal layer must not include:

- scenario-specific role/resource names as repair triggers;
- dataset-specific policy facts;
- hidden expected answers;
- rules that only work for iTrust, IBM, CyberChair, healthcare, gradebook, or
  any other named corpus;
- prompt text that nudges the model toward a known benchmark answer without
  deriving that nudge from the reviewed source and verifier evidence.

## Change Gate

Before adding any new signal-layer, prompt, review, repair, or convergence
behavior, answer these questions in the implementation notes or commit message:

1. What verifier output or reviewed source evidence caused this change?
2. Would this still work if all domain nouns were renamed?
3. Is this a general structural repair signal, or scenario knowledge?
4. Could this contaminate an evaluation claim?
5. Is the behavior covered by a neutral test using domain-renamed examples?

If any answer is unclear, stop and ask before implementing.

## Setback Protocol

If an experiment or implementation run gets stuck, use this protocol:

1. State exactly what failed.
2. State why it matters for the claim or run.
3. Separate setup failures, model failures, verifier failures, schema gaps, and
   genuine policy-intent conflicts.
4. Offer honest options, including stopping, rerunning, asking for human
   judgment, or changing the architecture.
5. Wait for direction before adding any shortcut that changes the semantics of
   the run.
