"""Source-document DAG support for AutoCedar authoring.

This module is deliberately deterministic. It does not decide policy intent;
it turns a raw requirements document into stable source nodes and bounded
context packets so the LLM proposes atoms from a local, auditable slice instead
of repeatedly ingesting the whole document.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Iterable

from autocedar.atoms import PropertyAtom, to_dict
from autocedar.corpus import AtomDecision


_AUTHZ_KEYWORDS = (
    "access",
    "allow",
    "allowed",
    "authorize",
    "authorized",
    "can",
    "cannot",
    "deny",
    "forbid",
    "may",
    "must",
    "only",
    "permit",
    "prevent",
    "read",
    "record",
    "register",
    "submit",
    "update",
    "view",
)

_STOPWORDS = {
    "able",
    "about",
    "after",
    "again",
    "also",
    "and",
    "any",
    "are",
    "because",
    "been",
    "before",
    "being",
    "but",
    "can",
    "cannot",
    "during",
    "each",
    "for",
    "from",
    "has",
    "have",
    "her",
    "his",
    "into",
    "may",
    "must",
    "not",
    "only",
    "or",
    "other",
    "own",
    "shall",
    "she",
    "such",
    "that",
    "the",
    "their",
    "then",
    "there",
    "they",
    "this",
    "time",
    "use",
    "user",
    "will",
    "with",
}


@dataclass
class SourceNode:
    """One stable, line-addressable source slice."""

    id: str
    text: str
    start_line: int
    end_line: int
    heading_path: list[str] = field(default_factory=list)
    node_type: str = "paragraph"
    parent_id: str | None = None
    ordinal: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "text": self.text,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "heading_path": list(self.heading_path),
            "node_type": self.node_type,
            "parent_id": self.parent_id,
            "ordinal": self.ordinal,
        }


@dataclass
class SourceDocument:
    """Parsed requirements document with graph edges between source nodes."""

    nodes: list[SourceNode]
    edges: list[dict[str, str]]

    @property
    def by_id(self) -> dict[str, SourceNode]:
        return {node.id: node for node in self.nodes}

    def authorization_nodes(self) -> list[SourceNode]:
        nodes = [node for node in self.nodes if _looks_authorization_relevant(node.text)]
        return nodes or list(self.nodes)

    def to_index(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "nodes": [node.to_dict() for node in self.nodes],
            "edges": list(self.edges),
            "summary": {
                "nodes": len(self.nodes),
                "authorization_relevant_nodes": len(self.authorization_nodes()),
            },
        }


@dataclass
class SourcePacket:
    """Bounded context sent to a proposer for one graph-frontier expansion."""

    id: str
    kind: str
    focus_node_ids: list[str]
    nodes: list[SourceNode]
    related_nodes: list[SourceNode] = field(default_factory=list)
    approved_schema_atoms: list[str] = field(default_factory=list)
    approved_property_atoms: list[str] = field(default_factory=list)
    prior_decisions: list[str] = field(default_factory=list)

    def node_ids(self) -> list[str]:
        return list(dict.fromkeys([*self.focus_node_ids, *[n.id for n in self.related_nodes]]))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "focus_node_ids": list(self.focus_node_ids),
            "nodes": [node.to_dict() for node in self.nodes],
            "related_nodes": [node.to_dict() for node in self.related_nodes],
            "approved_schema_atoms": list(self.approved_schema_atoms),
            "approved_property_atoms": list(self.approved_property_atoms),
            "prior_decisions": list(self.prior_decisions),
        }

    def to_prompt_text(self) -> str:
        focus = "\n\n".join(_format_source_node(node) for node in self.nodes)
        related = "\n\n".join(_format_source_node(node) for node in self.related_nodes)
        schema_atoms = "\n".join(f"- {name}" for name in self.approved_schema_atoms) or "- none yet"
        property_atoms = "\n".join(f"- {name}" for name in self.approved_property_atoms) or "- none yet"
        decisions = "\n".join(f"- {item}" for item in self.prior_decisions[-12:]) or "- none yet"
        return (
            f"<autocedar_source_packet id=\"{self.id}\" kind=\"{self.kind}\">\n"
            "This is a bounded packet from a larger requirements document. "
            "Do not infer intent from unavailable document text. Ground every "
            "proposed atom in the source ids shown here, and include those ids "
            "in the atom's source_excerpt when possible.\n\n"
            "Focus source nodes:\n"
            f"{focus}\n\n"
            "Related source nodes from the intent DAG neighborhood:\n"
            f"{related or '- none'}\n\n"
            "Approved schema atoms so far:\n"
            f"{schema_atoms}\n\n"
            "Approved property atoms so far:\n"
            f"{property_atoms}\n\n"
            "Recent review decisions:\n"
            f"{decisions}\n"
            "</autocedar_source_packet>\n"
        )


def compile_source_document(spec_text: str) -> SourceDocument:
    """Split raw prose into stable source nodes plus local DAG edges."""

    lines = spec_text.splitlines()
    nodes: list[SourceNode] = []
    edges: list[dict[str, str]] = []
    headings: list[str] = []
    paragraph: list[tuple[int, str]] = []
    ordinal = 0

    def flush_paragraph() -> None:
        nonlocal paragraph, ordinal
        if not paragraph:
            return
        blocks = _paragraph_blocks(paragraph)
        paragraph = []
        for text, start, end in blocks:
            if not text:
                continue
            for chunk_text, chunk_start, chunk_end in _split_requirement_block(text, start, end):
                ordinal += 1
                node = SourceNode(
                    id=_node_id(headings, ordinal, chunk_start),
                    text=chunk_text,
                    start_line=chunk_start,
                    end_line=chunk_end,
                    heading_path=list(headings),
                    node_type="requirement",
                    parent_id=_section_id(headings),
                    ordinal=ordinal,
                )
                nodes.append(node)

    for line_no, raw_line in enumerate(lines, start=1):
        stripped = raw_line.strip()
        heading = _parse_heading(stripped)
        if heading is not None:
            flush_paragraph()
            level, title = heading
            headings = headings[: max(0, level - 1)]
            headings.append(title)
            continue
        if not stripped:
            flush_paragraph()
            continue
        paragraph.append((line_no, raw_line))
    flush_paragraph()

    for prev, nxt in zip(nodes, nodes[1:]):
        edges.append({"source": prev.id, "target": nxt.id, "type": "next_sibling"})
        if prev.parent_id and prev.parent_id == nxt.parent_id:
            edges.append({"source": prev.id, "target": nxt.id, "type": "same_section"})
    for node in nodes:
        if node.parent_id:
            edges.append({"source": node.parent_id, "target": node.id, "type": "contains"})

    return SourceDocument(nodes=nodes, edges=edges)


def build_schema_packets(
    doc: SourceDocument,
    *,
    approved_schema_atoms: Iterable[Any] = (),
    max_chars: int = 6000,
) -> list[SourcePacket]:
    """Group source nodes into section-sized packets for schema atom deltas."""

    grouped: dict[str, list[SourceNode]] = {}
    for node in doc.nodes:
        key = node.parent_id or "section:root"
        grouped.setdefault(key, []).append(node)

    packets: list[SourcePacket] = []
    approved_names = [_atom_name(atom) for atom in approved_schema_atoms]
    for section_index, (_, section_nodes) in enumerate(grouped.items(), start=1):
        chunk: list[SourceNode] = []
        current_chars = 0
        part = 1
        for node in section_nodes:
            next_chars = current_chars + len(node.text)
            if chunk and next_chars > max_chars:
                packets.append(
                    _make_packet(
                        kind="schema",
                        ordinal=len(packets) + 1,
                        focus_nodes=chunk,
                        related_nodes=_neighbors(doc, chunk),
                        approved_schema_atoms=approved_names,
                    ),
                )
                chunk = []
                current_chars = 0
                part += 1
            chunk.append(node)
            current_chars += len(node.text)
        if chunk:
            packet = _make_packet(
                kind="schema",
                ordinal=len(packets) + 1,
                focus_nodes=chunk,
                related_nodes=_neighbors(doc, chunk),
                approved_schema_atoms=approved_names,
            )
            if part > 1:
                packet.id = f"{packet.id}.part{part}"
            packets.append(packet)
        _ = section_index
    return packets or [
        SourcePacket(
            id="schema.empty",
            kind="schema",
            focus_node_ids=[],
            nodes=[],
            approved_schema_atoms=approved_names,
        ),
    ]


def select_property_packet(
    doc: SourceDocument,
    node: SourceNode,
    *,
    approved_schema_atoms: Iterable[Any] = (),
    approved_property_atoms: Iterable[PropertyAtom] = (),
    prior_decisions: Iterable[AtomDecision] = (),
) -> SourcePacket:
    """Build a one-focus-node property packet from DAG neighborhood edges."""

    return _make_packet(
        kind="property",
        ordinal=node.ordinal,
        focus_nodes=[node],
        related_nodes=_neighbors(doc, [node]),
        approved_schema_atoms=[_atom_name(atom) for atom in approved_schema_atoms],
        approved_property_atoms=[_atom_name(atom) for atom in approved_property_atoms],
        prior_decisions=[_decision_summary(decision) for decision in prior_decisions],
    )


def build_coverage_ledger(
    doc: SourceDocument,
    *,
    completed_property_node_ids: set[str],
    schema_packets: list[SourcePacket],
    property_packets: list[SourcePacket],
) -> dict[str, Any]:
    auth_ids = [node.id for node in doc.authorization_nodes()]
    return {
        "schema_version": 1,
        "source_nodes": len(doc.nodes),
        "authorization_nodes": auth_ids,
        "schema_packet_ids": [packet.id for packet in schema_packets],
        "property_packet_ids": [packet.id for packet in property_packets],
        "completed_property_node_ids": sorted(completed_property_node_ids),
        "open_property_node_ids": [
            node_id for node_id in auth_ids if node_id not in completed_property_node_ids
        ],
    }


def build_source_intent_dag(
    doc: SourceDocument,
    *,
    schema_packets: list[SourcePacket],
    property_packets: list[SourcePacket],
    schema_atoms: Iterable[Any] = (),
    property_atoms: Iterable[PropertyAtom] = (),
    schema_gaps: Iterable[dict[str, Any]] = (),
) -> dict[str, Any]:
    schema_atom_list = list(schema_atoms)
    property_atom_list = list(property_atoms)
    schema_gap_list = list(schema_gaps)
    nodes: list[dict[str, Any]] = [
        {
            "id": "document",
            "kind": "document",
            "summary": "raw requirements document",
        },
    ]
    edges: list[dict[str, str]] = [{"source": "document", "target": node.id, "type": "contains"} for node in doc.nodes]
    nodes.extend(node.to_dict() | {"kind": "source"} for node in doc.nodes)
    edges.extend(doc.edges)
    for packet in [*schema_packets, *property_packets]:
        nodes.append(
            {
                "id": f"packet:{packet.id}",
                "kind": f"{packet.kind}_packet",
                "focus_node_ids": list(packet.focus_node_ids),
            },
        )
        for source_id in packet.focus_node_ids:
            edges.append(
                {
                    "source": source_id,
                    "target": f"packet:{packet.id}",
                    "type": "expands_into",
                },
            )
        for source_id in [node.id for node in packet.related_nodes]:
            edges.append(
                {
                    "source": source_id,
                    "target": f"packet:{packet.id}",
                    "type": "context_for",
                },
            )
    for atom_node in atoms_as_graph_nodes(schema_atom_list, "schema_atom"):
        nodes.append(atom_node)
        for source_id in atom_node["source_node_ids"]:
            edges.append(
                {
                    "source": source_id,
                    "target": atom_node["id"],
                    "type": "grounds_schema_atom",
                },
            )
    for atom_node in atoms_as_graph_nodes(property_atom_list, "property_atom"):
        nodes.append(atom_node)
        for source_id in atom_node["source_node_ids"]:
            edges.append(
                {
                    "source": source_id,
                    "target": atom_node["id"],
                    "type": "grounds_property_atom",
                },
            )
    for index, gap in enumerate(schema_gap_list, start=1):
        gap_id = f"schema_gap:{index}:{gap.get('atom_name', 'unknown')}"
        nodes.append(
            {
                "id": gap_id,
                "kind": "schema_gap",
                "gap": dict(gap),
            },
        )
        atom_name = gap.get("atom_name")
        if atom_name:
            edges.append(
                {
                    "source": f"property_atom:{atom_name}",
                    "target": gap_id,
                    "type": "reveals_schema_gap",
                },
            )
    return {
        "schema_version": 1,
        "nodes": nodes,
        "edges": edges,
        "summary": {
            "source_nodes": len(doc.nodes),
            "schema_packets": len(schema_packets),
            "property_packets": len(property_packets),
            "schema_atoms": len(schema_atom_list),
            "property_atoms": len(property_atom_list),
            "schema_gaps": len(schema_gap_list),
        },
    }


def approved_target_spec(
    *,
    original_spec_name: str,
    schema_atoms: Iterable[Any],
    property_atoms: Iterable[PropertyAtom],
) -> str:
    """Create the Stage 3 prose target from reviewed atoms, not raw prose."""

    schema_lines = [
        f"- {atom.name}: {getattr(atom, 'plain_english_summary', '')} "
        f"(source_ids: {', '.join(atom_source_ids(atom)) or 'unknown'}; "
        f"source: {getattr(atom, 'source_excerpt', '')})"
        for atom in schema_atoms
    ]
    property_lines = [
        (
            f"- {atom.name} [{atom.constraint_type}]: {atom.plain_english_summary} "
            f"(action={atom.action}; principals={', '.join(atom.principal_types) or 'any'}; "
            f"resources={', '.join(atom.resource_types) or 'any'}; "
            f"source_ids={', '.join(atom_source_ids(atom)) or 'unknown'}; "
            f"source={atom.source_excerpt})"
        )
        for atom in property_atoms
    ]
    return (
        "# AutoCedar Approved Intent Target\n\n"
        "This Stage 3 specification is generated from HITL/AITL-approved "
        "schema and property atoms. The raw input document remains archived "
        f"as `{original_spec_name}` in the session input directory, but policy "
        "synthesis must satisfy the reviewed formal target below rather than "
        "reinterpreting the raw prose.\n\n"
        "## Approved Schema Atoms\n"
        f"{chr(10).join(schema_lines) if schema_lines else '- supplied schema; no Stage 1 atoms'}\n\n"
        "## Approved Property Atoms\n"
        f"{chr(10).join(property_lines) if property_lines else '- no approved property atoms'}\n"
    )


def _make_packet(
    *,
    kind: str,
    ordinal: int,
    focus_nodes: list[SourceNode],
    related_nodes: list[SourceNode],
    approved_schema_atoms: list[str] | None = None,
    approved_property_atoms: list[str] | None = None,
    prior_decisions: list[str] | None = None,
) -> SourcePacket:
    focus_ids = [node.id for node in focus_nodes]
    return SourcePacket(
        id=f"{kind}.{ordinal:04d}",
        kind=kind,
        focus_node_ids=focus_ids,
        nodes=focus_nodes,
        related_nodes=related_nodes,
        approved_schema_atoms=approved_schema_atoms or [],
        approved_property_atoms=approved_property_atoms or [],
        prior_decisions=prior_decisions or [],
    )


def _neighbors(doc: SourceDocument, focus_nodes: list[SourceNode], limit: int = 6) -> list[SourceNode]:
    if not focus_nodes:
        return []
    focus_ids = {node.id for node in focus_nodes}
    related: list[SourceNode] = []
    all_nodes = doc.nodes
    positions = {node.id: index for index, node in enumerate(all_nodes)}
    terms = set().union(*(_terms(node.text) for node in focus_nodes))

    for node in focus_nodes:
        index = positions[node.id]
        for candidate_index in (index - 1, index + 1):
            if 0 <= candidate_index < len(all_nodes):
                candidate = all_nodes[candidate_index]
                if candidate.id not in focus_ids:
                    related.append(candidate)

    scored: list[tuple[int, SourceNode]] = []
    for candidate in all_nodes:
        if candidate.id in focus_ids:
            continue
        score = len(terms & _terms(candidate.text))
        if candidate.parent_id and candidate.parent_id in {node.parent_id for node in focus_nodes}:
            score += 2
        if score > 1:
            scored.append((score, candidate))
    scored.sort(key=lambda item: (-item[0], item[1].ordinal))
    related.extend(candidate for _, candidate in scored[:limit])
    deduped: list[SourceNode] = []
    seen: set[str] = set()
    for node in related:
        if node.id in seen or node.id in focus_ids:
            continue
        seen.add(node.id)
        deduped.append(node)
        if len(deduped) >= limit:
            break
    return deduped


def _format_source_node(node: SourceNode) -> str:
    heading = " / ".join(node.heading_path) if node.heading_path else "root"
    return (
        f"[source_id: {node.id}; lines: {node.start_line}-{node.end_line}; "
        f"section: {heading}]\n{node.text}"
    )


def _looks_authorization_relevant(text: str) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in _AUTHZ_KEYWORDS)


def _terms(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[A-Za-z][A-Za-z0-9_]{2,}", text.lower())
        if token not in _STOPWORDS
    }


def _parse_heading(stripped: str) -> tuple[int, str] | None:
    markdown = re.match(r"^(#{1,6})\s+(.+)$", stripped)
    if markdown:
        return len(markdown.group(1)), markdown.group(2).strip()
    if stripped.endswith(":") and len(stripped) < 120 and not re.search(r"[.;]", stripped):
        return 2, stripped[:-1].strip()
    return None


def _normalize_block(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _paragraph_blocks(paragraph: list[tuple[int, str]]) -> list[tuple[str, int, int]]:
    if len(paragraph) <= 1:
        if not paragraph:
            return []
        line_no, text = paragraph[0]
        return [(_normalize_block(text), line_no, line_no)]
    return [
        (_normalize_block(text), line_no, line_no)
        for line_no, text in paragraph
        if _normalize_block(text)
    ]


def _split_requirement_block(
    text: str,
    start_line: int,
    end_line: int,
    max_chars: int = 900,
) -> list[tuple[str, int, int]]:
    sentences = [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s*(?=[A-Z0-9\"'])", text)
        if sentence.strip()
    ]
    if len(sentences) > 1:
        return [(sentence, start_line, end_line) for sentence in sentences]
    return _split_long_block(text, start_line, end_line, max_chars=max_chars)


def _split_long_block(text: str, start_line: int, end_line: int, max_chars: int = 1800) -> list[tuple[str, int, int]]:
    if len(text) <= max_chars:
        return [(text, start_line, end_line)]
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks: list[tuple[str, int, int]] = []
    current: list[str] = []
    for sentence in sentences:
        if current and sum(len(part) + 1 for part in current) + len(sentence) > max_chars:
            chunks.append((" ".join(current).strip(), start_line, end_line))
            current = []
        current.append(sentence)
    if current:
        chunks.append((" ".join(current).strip(), start_line, end_line))
    return chunks


def _section_id(headings: list[str]) -> str | None:
    if not headings:
        return None
    return "section:" + ".".join(_slug(part) for part in headings)


def _node_id(headings: list[str], ordinal: int, start_line: int) -> str:
    prefix = ".".join(_slug(part) for part in headings[-2:] if part) or "root"
    return f"src.{prefix}.p{ordinal:04d}.l{start_line}"


def _slug(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return slug[:48] or "section"


def _atom_name(atom: Any) -> str:
    if isinstance(atom, dict):
        return str(atom.get("name", ""))
    return str(getattr(atom, "name", ""))


def _decision_summary(decision: AtomDecision) -> str:
    return f"{decision.atom_name}: {decision.action} {decision.reason}".strip()


def atom_source_ids(atom: Any) -> list[str]:
    """Best-effort source id extraction from a reviewed atom's source excerpt."""

    explicit_ids = getattr(atom, "_source_node_ids", [])
    if isinstance(explicit_ids, list):
        explicit = [str(source_id) for source_id in explicit_ids if str(source_id)]
    else:
        explicit = []
    source_excerpt = getattr(atom, "source_excerpt", "")
    return list(dict.fromkeys([*explicit, *source_ids_from_text(source_excerpt)]))


def source_ids_from_text(text: str) -> list[str]:
    """Extract source ids from packet or atom text."""

    return list(dict.fromkeys(re.findall(r"src\.[A-Za-z0-9_.-]+", text)))


def attach_source_ids(atom: Any, source_ids: Iterable[str]) -> Any:
    """Attach source ids to a mutable atom without rewriting its excerpt."""

    ids = [source_id for source_id in dict.fromkeys(source_ids) if source_id]
    if not ids:
        return atom
    existing = atom_source_ids(atom)
    missing = [source_id for source_id in ids if source_id not in existing]
    if not missing:
        return atom
    setattr(atom, "_source_node_ids", [*existing, *missing])
    return atom


def atoms_as_graph_nodes(atoms: Iterable[Any], kind: str) -> list[dict[str, Any]]:
    return [
        {
            "id": f"{kind}:{_atom_name(atom)}",
            "kind": kind,
            "atom": to_dict(atom),
            "source_node_ids": atom_source_ids(atom),
        }
        for atom in atoms
    ]
