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
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test123")
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


def test_apikey_command_writes_env_file(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    env_path = tmp_path / ".env"

    rc = cli._cmd_apikey(
        argparse.Namespace(
            key="sk-ant-test123",
            env=env_path,
            clear=False,
        ),
    )

    assert rc == 0
    assert env_path.read_text() == "ANTHROPIC_API_KEY=sk-ant-test123\n"
    assert "sk-ant-test123" not in capsys.readouterr().out


def test_apikey_command_replaces_existing_value(tmp_path: Path) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text("ANTHROPIC_API_KEY=sk-ant-...\nAUTOCEDAR_EFFORT=high\n")

    cli._cmd_apikey(
        argparse.Namespace(
            key="sk-ant-realvalue",
            env=env_path,
            clear=False,
        ),
    )

    assert env_path.read_text() == "ANTHROPIC_API_KEY=sk-ant-realvalue\nAUTOCEDAR_EFFORT=high\n"


def test_apikey_command_rejects_placeholder(tmp_path: Path) -> None:
    with pytest.raises(SystemExit):
        cli._cmd_apikey(
            argparse.Namespace(
                key="sk-ant-...",
                env=tmp_path / ".env",
                clear=False,
            ),
        )


def test_parser_exposes_apikey_command() -> None:
    parser = cli._build_parser()
    args = parser.parse_args(["api-key", "sk-ant-test123", "--env", "local.env"])

    assert args.key == "sk-ant-test123"
    assert args.env == Path("local.env")
    assert args.func is cli._cmd_apikey
