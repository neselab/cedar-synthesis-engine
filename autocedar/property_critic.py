"""Stage 2 decomposition critic for proposed property atoms.

This is the AutoCedar analogue of LEAP's planning-level reviewer: the verifier
can tell us whether an atom is formally well shaped, but not whether the atom is
useful, non-redundant, or scoped tightly enough to be worth putting in front of
the human reviewer. The critic is deliberately advisory. It can reject weak
decompositions before HITL review, but accepted atoms still require normal
symbolic grounding and human intent review.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


CritiqueDecision = Literal["accept", "repair", "reject"]


@dataclass
class PropertyCritique:
    """Planning-level assessment of a proposed Stage 2 property atom."""

    decision: CritiqueDecision
    reason: str
    tags: list[str] = field(default_factory=list)

    @property
    def accepted(self) -> bool:
        return self.decision == "accept"

    @property
    def wants_repair(self) -> bool:
        return self.decision == "repair"

    @property
    def rejected(self) -> bool:
        return self.decision == "reject"


def accept_property_atom() -> PropertyCritique:
    """Default no-op critic used when no live reviewer is configured."""

    return PropertyCritique(
        decision="accept",
        reason="No decomposition critic configured; defer to symbolic and HITL review.",
        tags=["not-configured"],
    )
