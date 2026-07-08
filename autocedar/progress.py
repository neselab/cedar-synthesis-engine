"""Small formatting helpers for long-running AutoCedar progress events."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def format_property_progress(payload: Mapping[str, Any]) -> str:
    """Return a compact, user-facing summary for Stage 2 property progress."""

    event = str(payload.get("event") or "progress").replace("_", " ")
    source_index = payload.get("source_index")
    source_total = payload.get("source_total")
    source_completed = payload.get("source_completed", 0)
    source_open = payload.get("source_open")

    if source_index is not None and source_total:
        source = f"source {source_index}/{source_total}"
    elif source_total:
        source = f"{source_completed}/{source_total} sources complete"
    else:
        source = "source progress unknown"

    parts = [event, source]
    if source_open is not None:
        parts.append(f"open {source_open}")

    approved = payload.get("approved")
    decisions = payload.get("decisions")
    rejected = payload.get("rejected")
    if approved is not None:
        parts.append(f"approved {approved}")
    if rejected is not None:
        parts.append(f"rejected {rejected}")
    if decisions is not None:
        parts.append(f"decisions {decisions}")

    bundle_size = payload.get("bundle_size")
    queued = payload.get("queued")
    if bundle_size is not None:
        parts.append(f"bundle {bundle_size}")
    if queued:
        parts.append(f"queued {queued}")

    atom_name = payload.get("atom_name")
    decision = payload.get("decision")
    if atom_name:
        atom_text = f"atom {atom_name}"
        if decision:
            atom_text = f"{atom_text} {decision}"
        parts.append(atom_text)

    reason = payload.get("reason")
    if reason:
        reason_text = " ".join(str(reason).split())
        parts.append(f"reason {reason_text[:90]}")

    return " | ".join(parts)
