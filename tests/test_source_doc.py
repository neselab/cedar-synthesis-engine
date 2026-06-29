from __future__ import annotations

from autocedar.atoms import PropertyAtom
from autocedar.source_doc import (
    attach_source_ids,
    atom_source_ids,
    build_schema_packets,
    compile_source_document,
    select_property_packet,
)


def test_compile_source_document_splits_pasted_requirement_sentences() -> None:
    spec = (
        "Doctors can read records for patients on their care team."
        "Nurses can update vitals only during their shift."
        "Patients can view their own records."
    )

    doc = compile_source_document(spec)

    assert [node.text for node in doc.nodes] == [
        "Doctors can read records for patients on their care team.",
        "Nurses can update vitals only during their shift.",
        "Patients can view their own records.",
    ]
    assert len(doc.authorization_nodes()) == 3
    assert all(node.id.startswith("src.root.") for node in doc.nodes)


def test_context_packet_uses_dag_neighbors_without_full_document_blob() -> None:
    spec = """# Registration

Students can add courses during add/drop.
Students cannot add courses after registration closes.

# Registrar

The registrar can close registration.
"""
    doc = compile_source_document(spec)
    packet = select_property_packet(doc, doc.authorization_nodes()[1])
    text = packet.to_prompt_text()

    assert packet.focus_node_ids == [doc.nodes[1].id]
    assert doc.nodes[0].id in [node.id for node in packet.related_nodes]
    assert "Students cannot add courses after registration closes." in text
    assert "<autocedar_source_packet" in text


def test_schema_packets_are_section_bounded() -> None:
    spec = """# Students

Students can register.

# Professors

Professors can enter grades.
"""
    doc = compile_source_document(spec)
    packets = build_schema_packets(doc)

    assert len(packets) == 2
    assert packets[0].focus_node_ids == [doc.nodes[0].id]
    assert packets[1].focus_node_ids == [doc.nodes[1].id]


def test_attach_source_ids_keeps_visible_excerpt_unchanged() -> None:
    atom = PropertyAtom(
        name="owner_floor",
        rationale="owner path",
        plain_english_summary="Owners can read their documents.",
        source_excerpt="The owner can read the document.",
        constraint_type="floor",
        action="read",
        principal_types=["User"],
        resource_types=["Document"],
        reference_cedar='permit (principal, action == Action::"read", resource);',
    )

    attach_source_ids(atom, ["src.docs.p0001.l7"])

    assert atom.source_excerpt == "The owner can read the document."
    assert atom_source_ids(atom) == ["src.docs.p0001.l7"]
