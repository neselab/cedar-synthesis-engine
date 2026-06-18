from __future__ import annotations

import argparse
from pathlib import Path
from types import SimpleNamespace

import pytest

import autocedar.cli as cli


def test_author_command_injects_harness_synthesizer(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    spec = tmp_path / "spec.md"
    spec.write_text("Owners can read their own resources.")
    schema = tmp_path / "schema.cedarschema"
    schema.write_text("entity User;")

    sentinel_synthesizer = object()
    captured: dict[str, object] = {}

    monkeypatch.setattr(cli, "LLMClient", lambda **kwargs: object())
    monkeypatch.setattr(
        cli,
        "make_harness_synthesizer",
        lambda **kwargs: sentinel_synthesizer,
    )

    def fake_author_pipeline(**kwargs: object) -> SimpleNamespace:
        captured.update(kwargs)
        return SimpleNamespace(
            session_dir=tmp_path / "out" / "session",
            candidate_path=tmp_path / "out" / "session" / "candidate.cedar",
            final_user_approved=True,
            notes=[],
        )

    monkeypatch.setattr(cli, "author_pipeline", fake_author_pipeline)

    rc = cli._cmd_author(
        argparse.Namespace(
            spec=str(spec),
            out=str(tmp_path / "out"),
            session_id=None,
            schema=str(schema),
            model="claude-test",
            effort="high",
            auto_approve=True,
        ),
    )

    assert rc == 0
    assert captured["synthesize"] is sentinel_synthesizer
    assert captured["schema_path_override"] == str(schema)
    assert "repair_property_atom" in captured


def test_doctor_command_returns_nonzero_on_failed_check(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "autocedar.doctor.run_doctor",
        lambda live_symcc=True: SimpleNamespace(failed=True),
    )
    monkeypatch.setattr(
        "autocedar.doctor.format_doctor_report",
        lambda report: "doctor failed",
    )

    rc = cli._cmd_doctor(argparse.Namespace(no_live_symcc=False))

    assert rc == 1


def test_parser_exposes_doctor_command() -> None:
    parser = cli._build_parser()
    args = parser.parse_args(["doctor", "--no-live-symcc"])

    assert args.no_live_symcc is True
    assert args.func is cli._cmd_doctor
