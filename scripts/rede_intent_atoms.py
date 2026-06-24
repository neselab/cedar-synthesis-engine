#!/usr/bin/env python3
"""Extract weak intent atoms from REDE AccessControlModelStudy labels.

The REDE corpus is external data; this script expects a local checkout and
does not vendor any REDE files into AutoCedar. It parses the labeled
``*ac rules.txt`` exports into JSONL records that can seed AutoCedar
schema/property atomization experiments.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

SENTENCE_RE = re.compile(r"^\s*(?P<id>\d+(?:\.\d+)?):(?P<text>.*)$")
CRUD_ORDER = ("C", "R", "U", "D", "E")


@dataclass(frozen=True)
class RedeIntentAtom:
    """One weakly labeled access-control intent from REDE."""

    dataset: str
    source_file: str
    sentence_id: str
    sentence: str
    subject_text: str
    action_text: str
    resource_text: str
    negated: bool
    crud: str
    crud_ops: list[str]
    raw_triple: str


def _dataset_name(path: Path) -> str:
    name = path.stem
    for suffix in (" - ac rules",):
        if name.endswith(suffix):
            name = name[: -len(suffix)]
    return name


def _crud_ops(crud: str) -> list[str]:
    seen: list[str] = []
    for ch in crud.upper():
        if ch in CRUD_ORDER and ch not in seen:
            seen.append(ch)
    return seen


def _parse_triple_line(
    *,
    dataset: str,
    source_file: str,
    sentence_id: str,
    sentence: str,
    raw_line: str,
) -> RedeIntentAtom | None:
    text = raw_line.strip()
    if ";" not in text:
        return None

    if " - " in text:
        triple_text, crud_text = text.rsplit(" - ", 1)
    else:
        triple_text, crud_text = text, ""

    fields = [field.strip() for field in triple_text.split(";")]
    if len(fields) < 3:
        return None

    subject, action, resource = fields[:3]
    negated = any(field.upper().startswith("NEG-") for field in fields[3:])
    crud = crud_text.strip().upper()

    return RedeIntentAtom(
        dataset=dataset,
        source_file=source_file,
        sentence_id=sentence_id,
        sentence=sentence.strip(),
        subject_text=subject,
        action_text=action,
        resource_text=resource,
        negated=negated,
        crud=crud,
        crud_ops=_crud_ops(crud),
        raw_triple=text,
    )


def parse_rule_export(path: Path) -> list[RedeIntentAtom]:
    """Parse one REDE labeled text export."""
    dataset = _dataset_name(path)
    source_file = path.name
    current_sentence_id = ""
    current_sentence = ""
    atoms: list[RedeIntentAtom] = []

    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not raw_line.strip():
            continue

        sentence_match = SENTENCE_RE.match(raw_line)
        if sentence_match:
            current_sentence_id = sentence_match.group("id")
            current_sentence = sentence_match.group("text").strip()
            continue

        atom = _parse_triple_line(
            dataset=dataset,
            source_file=source_file,
            sentence_id=current_sentence_id,
            sentence=current_sentence,
            raw_line=raw_line,
        )
        if atom is not None:
            atoms.append(atom)

    return atoms


def find_rule_exports(access_control_study_dir: Path) -> list[Path]:
    """Find labeled REDE text exports under AccessControlModelStudy."""
    label_dir = access_control_study_dir / "labelled data sets"
    if not label_dir.exists():
        raise FileNotFoundError(f"missing labeled data directory: {label_dir}")
    return sorted(label_dir.glob("*.txt"))


def count_sentence_lines(path: Path) -> int:
    """Count sentence records in one labeled text export."""
    return sum(
        1
        for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines()
        if SENTENCE_RE.match(raw_line)
    )


def summarize(
    atoms: Iterable[RedeIntentAtom],
    sentence_line_counts: dict[str, int] | None = None,
) -> dict[str, object]:
    """Build a compact dataset summary."""
    by_dataset: dict[str, Counter[str]] = defaultdict(Counter)
    crud_counts: Counter[str] = Counter()
    total = 0
    empty_subject = 0
    negated = 0
    unique_subjects: dict[str, set[str]] = defaultdict(set)
    unique_actions: dict[str, set[str]] = defaultdict(set)
    unique_resources: dict[str, set[str]] = defaultdict(set)
    sentence_ids: dict[str, set[str]] = defaultdict(set)

    for atom in atoms:
        total += 1
        by_dataset[atom.dataset]["triples"] += 1
        if not atom.subject_text:
            empty_subject += 1
            by_dataset[atom.dataset]["empty_subject_triples"] += 1
        if atom.negated:
            negated += 1
            by_dataset[atom.dataset]["negated_triples"] += 1
        for op in atom.crud_ops:
            crud_counts[op] += 1
            by_dataset[atom.dataset][f"crud_{op}"] += 1
        if atom.subject_text:
            unique_subjects[atom.dataset].add(atom.subject_text)
        if atom.action_text:
            unique_actions[atom.dataset].add(atom.action_text)
        if atom.resource_text:
            unique_resources[atom.dataset].add(atom.resource_text)
        if atom.sentence_id:
            sentence_ids[atom.dataset].add(atom.sentence_id)

    dataset_summaries: dict[str, dict[str, int]] = {}
    for dataset, counts in sorted(by_dataset.items()):
        dataset_summaries[dataset] = dict(counts)
        if sentence_line_counts is not None:
            dataset_summaries[dataset]["sentence_lines"] = sentence_line_counts.get(
                dataset,
                0,
            )
        dataset_summaries[dataset]["access_control_sentence_lines"] = len(
            sentence_ids[dataset],
        )
        dataset_summaries[dataset]["unique_subjects"] = len(unique_subjects[dataset])
        dataset_summaries[dataset]["unique_actions"] = len(unique_actions[dataset])
        dataset_summaries[dataset]["unique_resources"] = len(unique_resources[dataset])

    return {
        "total_triples": total,
        "empty_subject_triples": empty_subject,
        "negated_triples": negated,
        "crud_counts": dict(sorted(crud_counts.items())),
        "datasets": dataset_summaries,
    }


def write_jsonl(path: Path, atoms: Iterable[RedeIntentAtom]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for atom in atoms:
            f.write(json.dumps(asdict(atom), ensure_ascii=False, sort_keys=True))
            f.write("\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Parse REDE AccessControlModelStudy labeled rules into intent atoms.",
    )
    parser.add_argument(
        "access_control_study_dir",
        type=Path,
        help="Path to REDE/data/AccessControlModelStudy.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("rede_intent_atoms.jsonl"),
        help="Output JSONL path.",
    )
    parser.add_argument(
        "--summary",
        type=Path,
        default=None,
        help="Optional summary JSON path.",
    )
    args = parser.parse_args()

    exports = find_rule_exports(args.access_control_study_dir)
    atoms: list[RedeIntentAtom] = []
    sentence_line_counts = {}
    for export in exports:
        sentence_line_counts[_dataset_name(export)] = count_sentence_lines(export)
        atoms.extend(parse_rule_export(export))

    write_jsonl(args.out, atoms)
    summary = summarize(atoms, sentence_line_counts=sentence_line_counts)
    if args.summary is not None:
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(
            json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    print(json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True))
    print(f"wrote {len(atoms)} atoms to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
