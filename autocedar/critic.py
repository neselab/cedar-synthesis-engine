"""Stage 3 LLM critic — intrinsic Cedar quality scoring.

See ``docs/HITL_STEP_B_PLAN.md`` §7.5 for context. The critic is a
quality oracle that runs *after* the symbolic verifier (which is the
correctness oracle); the two have non-overlapping authority. The
critic does NOT see:

- The verification plan or any reference policies.
- The original prose spec.
- The verifier's per-iteration feedback messages.

The critic sees only:

- The candidate Cedar text.
- The generic Cedar style guide (this module's constant).

Quality scoring is intrinsic — "is this idiomatic Cedar" — not
spec-relative. This is the load-bearing prompt boundary tested by
acceptance criterion 7 in §9.

For Step B the LLM call is a thin abstraction (``LLMScorer``) that
real implementations plug into. The default ``score_candidate`` runs
a stubbed LLM that returns a fixed mid-quality score so end-to-end
pipeline tests can run without a live LLM.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from statistics import mean
from typing import Callable

# ---------------------------------------------------------------------------
# Score data class.
# ---------------------------------------------------------------------------

CRITIC_DIMENSIONS = ("idiomatic", "minimal", "attribute_prefer", "maintainable")


@dataclass
class CriticScore:
    """Per-dimension score (1-5) plus a one-sentence rationale per dimension."""

    idiomatic: int
    minimal: int
    attribute_prefer: int
    maintainable: int
    rationales: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for dim in CRITIC_DIMENSIONS:
            v = getattr(self, dim)
            if not (1 <= v <= 5):
                raise ValueError(f"critic dimension {dim} = {v} is outside [1, 5]")

    @property
    def composite_mean(self) -> float:
        return mean(getattr(self, d) for d in CRITIC_DIMENSIONS)

    @property
    def composite_min(self) -> int:
        return min(getattr(self, d) for d in CRITIC_DIMENSIONS)

    def passes_threshold(self, mean_threshold: float = 4.0, min_threshold: int = 3) -> bool:
        """Default threshold per §7.5.2: mean ≥ 4.0 and no dim < 3."""
        return self.composite_mean >= mean_threshold and self.composite_min >= min_threshold


# ---------------------------------------------------------------------------
# Style guide (the only context outside the candidate the critic sees).
# ---------------------------------------------------------------------------

CRITIC_STYLE_GUIDE = """\
# Cedar style guide (generic; not derived from any specific spec)

Cedar is a permit-by-default-deny policy language. Idiomatic Cedar:

1. Prefers attribute references over hardcoded entity-ID enumeration.
   Good:    `principal.role == "admin"`
   Avoid:   `principal == User::"alice" || principal == User::"bob" || ...`

2. Uses `unless` for narrow exceptions on `permit when` rules, not
   nested boolean negation:
   Good:    `permit (...) when { ... } unless { resource.legalHold };`
   Avoid:   `permit (...) when { ... && !resource.legalHold };` (when an
            `unless` reads more clearly)

3. Uses `principal in Group` (entity-graph membership) for stable role
   structure; uses string-attribute role checks for simple flat roles.
   Both are idiomatic; pick the one that matches the schema's design.

4. Composes set predicates with the right operator:
   - `set.contains(elem)` for single-element membership
   - `set.containsAll(other)` for subset
   - `set.containsAny(other)` for non-empty intersection
   Cedar has no `.size()` operator.

5. Optional context attributes must be `has`-guarded before any read.
   Cedar's type-checker does not propagate negation through `has`,
   so the canonical guard pattern is
   `(!(context has X) || (context has X && context.X.field == ...))`.

6. Keep `when` clauses minimal. Redundant conjuncts (e.g. duplicate
   role checks across multiple permits) suggest refactoring to a
   shared helper attribute or to action groups.

7. Annotate non-obvious rules with `@id("...")` and
   `@description("...")`. These are first-class Cedar syntax and
   survive parsing.

# Quality dimensions to score (1-5 scale, with one-sentence rationale per dimension)

- idiomatic        — uses Cedar patterns from the docs; avoids
                     anti-patterns like entity-ID enumeration where
                     attribute references would be cleaner.
- minimal          — no redundant when-conditions or unreachable clauses.
- attribute_prefer — prefers attribute references over hardcoded
                     entity IDs or string disjunctions where attributes
                     exist.
- maintainable     — reasonable rule structure, optional `@id`/`@description`
                     annotations, named action groups where present.

For each dimension, output:
- A single integer 1-5 (1 = poor, 5 = excellent).
- A single-sentence rationale.

Output format: JSON object with keys "idiomatic", "minimal",
"attribute_prefer", "maintainable" each mapping to an object
``{"score": <int>, "rationale": "<one sentence>"}``.
"""


# ---------------------------------------------------------------------------
# Prompt builder — load-bearing boundary (§7.5.1).
# ---------------------------------------------------------------------------

def build_critic_prompt(candidate_cedar: str) -> str:
    """Build the critic's LLM prompt.

    The function signature is the boundary that enforces §7.5.1: the
    critic sees ONLY the candidate Cedar text and the (constant) style
    guide. Adding any further parameter to this function — for
    example, ``plan: VerificationPlanDraft`` or ``spec_text: str`` —
    would violate the design contract and break acceptance criterion 7.
    """
    return f"""\
You are scoring a Cedar policy on its intrinsic code quality. You are
NOT scoring whether it satisfies any particular access-control spec —
that is a separate verifier's job. Score on style alone.

{CRITIC_STYLE_GUIDE}

# Candidate Cedar policy

```cedar
{candidate_cedar}
```

Output your scores as a JSON object exactly matching the format
described in the style guide. Do not include any other prose.
"""


# ---------------------------------------------------------------------------
# Response parser.
# ---------------------------------------------------------------------------

def parse_critic_response(response_text: str) -> CriticScore:
    """Parse a critic LLM response into a CriticScore.

    Tolerant of the LLM wrapping the JSON in code fences. Raises
    ``ValueError`` if the response cannot be parsed or any score is
    out of range.
    """
    blob = _extract_json_block(response_text)
    data = json.loads(blob)
    scores: dict[str, int] = {}
    rationales: dict[str, str] = {}
    for dim in CRITIC_DIMENSIONS:
        if dim not in data:
            raise ValueError(f"critic response missing dimension {dim!r}")
        entry = data[dim]
        if isinstance(entry, dict):
            score_val = entry.get("score")
            rationale = entry.get("rationale", "")
        else:
            score_val = entry
            rationale = ""
        if not isinstance(score_val, int) or not (1 <= score_val <= 5):
            raise ValueError(f"critic {dim} score is not an int in [1, 5]: {score_val!r}")
        scores[dim] = score_val
        if rationale:
            rationales[dim] = str(rationale)
    return CriticScore(rationales=rationales, **scores)


_JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


def _extract_json_block(text: str) -> str:
    """Pull a JSON object out of LLM response text, with or without fences."""
    m = _JSON_BLOCK_RE.search(text)
    if m:
        return m.group(1)
    # Best-effort: find the first balanced JSON object.
    depth = 0
    start = -1
    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start != -1:
                return text[start : i + 1]
    raise ValueError("could not find JSON object in critic response")


# ---------------------------------------------------------------------------
# Stubbed LLM scorer (Step B).
# ---------------------------------------------------------------------------

LLMScorer = Callable[[str], str]


def stub_llm_scorer(prompt: str) -> str:
    """Step B placeholder LLM that returns a fixed mid-quality score.

    Real LLM integration lands in Step C/D. The stub exists so the
    end-to-end pipeline can be exercised in tests without a live API
    key, and so the critic-loop logic in Stage 3 (which compares
    scores across iterations) has something to compare.
    """
    _ = prompt  # silence unused
    return json.dumps(
        {
            "idiomatic": {
                "score": 4,
                "rationale": "stubbed score — real LLM integration in Step C/D",
            },
            "minimal": {"score": 4, "rationale": "stubbed"},
            "attribute_prefer": {"score": 4, "rationale": "stubbed"},
            "maintainable": {"score": 4, "rationale": "stubbed"},
        },
    )


def score_candidate(
    candidate_cedar: str,
    llm: LLMScorer = stub_llm_scorer,
) -> CriticScore:
    """End-to-end: build prompt → call LLM → parse → return CriticScore."""
    prompt = build_critic_prompt(candidate_cedar)
    response = llm(prompt)
    return parse_critic_response(response)


def to_dict(score: CriticScore) -> dict:
    """Serialize a CriticScore for corpus logging."""
    return asdict(score)
