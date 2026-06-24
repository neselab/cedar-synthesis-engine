from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_script_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "rede_intent_atoms.py"
    spec = importlib.util.spec_from_file_location("rede_intent_atoms", script_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_parse_rede_rule_export_counts_sentences_and_negation(tmp_path: Path) -> None:
    rede = _load_script_module()
    export = tmp_path / "Toy - ac rules.txt"
    export.write_text(
        "\n".join(
            [
                "1.0:Admins can create accounts.",
                "          admin;create;account - C",
                "2.0:Patients cannot edit passwords.",
                "          patient;edit;password;NEG-not - U",
                "3.0:This sentence has no access-control triple.",
                "",
            ],
        ),
        encoding="utf-8",
    )

    atoms = rede.parse_rule_export(export)
    assert len(atoms) == 2
    assert atoms[0].dataset == "Toy"
    assert atoms[0].crud_ops == ["C"]
    assert atoms[1].negated is True
    assert atoms[1].crud_ops == ["U"]
    assert rede.count_sentence_lines(export) == 3

    summary = rede.summarize(atoms, sentence_line_counts={"Toy": 3})
    assert summary["total_triples"] == 2
    assert summary["negated_triples"] == 1
    toy = summary["datasets"]["Toy"]
    assert toy["sentence_lines"] == 3
    assert toy["access_control_sentence_lines"] == 2
