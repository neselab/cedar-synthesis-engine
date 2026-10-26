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


def test_wrapped_list_items_and_prose_become_single_nodes() -> None:
    spec = (
        "## Requirements\n"
        "\n"
        "7. Reviewers can read other reviewers' reviews for a paper only after submitting\n"
        "   their own review for that paper.\n"
        "8. Reviewers can declare conflicts of interest for assigned papers.\n"
        "\n"
        "Chairs monitor the review process and may reassign papers when a reviewer\n"
        "withdraws.\n"
    )

    doc = compile_source_document(spec)

    assert [node.text for node in doc.nodes] == [
        "7. Reviewers can read other reviewers' reviews for a paper only after "
        "submitting their own review for that paper.",
        "8. Reviewers can declare conflicts of interest for assigned papers.",
        "Chairs monitor the review process and may reassign papers when a reviewer withdraws.",
    ]
    assert (doc.nodes[0].start_line, doc.nodes[0].end_line) == (3, 4)


def test_one_requirement_per_line_still_splits_per_line() -> None:
    spec = "Doctors read records\nNurses update vitals\nPatients view their own records\n"

    doc = compile_source_document(spec)

    assert [node.text for node in doc.nodes] == [
        "Doctors read records",
        "Nurses update vitals",
        "Patients view their own records",
    ]


def test_section_numbers_are_not_sentence_breaks() -> None:
    doc = compile_source_document("Owners bypass MFA except on confidential files (see §8.8). Admins can audit.")

    assert [node.text for node in doc.nodes] == [
        "Owners bypass MFA except on confidential files (see §8.8).",
        "Admins can audit.",
    ]
