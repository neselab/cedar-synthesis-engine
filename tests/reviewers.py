"""Stand-in reviewer for running the authoring pipeline offline in tests.

It approves any atom whose Cedar passed the symbolic checks without judging
meaning, so it exists only to exercise pipeline plumbing. Real runs use a
person or ``--model-review``.
"""

from __future__ import annotations

from typing import Any

from autocedar.atoms import PropertyAtom
from autocedar.corpus import AtomDecision


def approve_checked(atom: Any) -> AtomDecision:
    if isinstance(atom, PropertyAtom) and not atom.symbolic_verified:
        failed = [str(line) for line in atom.symbolic_verification_log or [] if "FAILED" in str(line)]
        return AtomDecision(
            atom_name=atom.name,
            action="reject",
            reason="Symbolic verification failed. " + " ".join(failed),
            symbolic_verified=False,
        )
    return AtomDecision(
        atom_name=getattr(atom, "name", "?"),
        action="approve",
        symbolic_verified=getattr(atom, "symbolic_verified", False),
    )
