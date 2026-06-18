from __future__ import annotations

import argparse
from pathlib import Path
from types import SimpleNamespace

import pytest

import autocedar.cli as cli


def test_parser_top_level_version(capsys: pytest.CaptureFixture[str]) -> None:
    parser = cli._build_parser()

    with pytest.raises(SystemExit) as exc:
        parser.parse_args(["--version"])

    assert exc.value.code == 0
    assert capsys.readouterr().out.strip() == f"autocedar {cli.__version__}"


def test_version_command_prints_installed_version(capsys: pytest.CaptureFixture[str]) -> None:
    rc = cli._cmd_version(argparse.Namespace())

    assert rc == 0
    assert capsys.readouterr().out.strip() == f"autocedar {cli.__version__}"


def test_parser_exposes_version_command() -> None:
    parser = cli._build_parser()
    args = parser.parse_args(["version"])

    assert args.func is cli._cmd_version


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


def test_parser_exposes_setup_command() -> None:
    parser = cli._build_parser()
    args = parser.parse_args(["setup", "--yes", "--skip-cvc5"])

    assert args.yes is True
    assert args.skip_cvc5 is True
    assert args.func is cli._cmd_setup


def test_setup_dry_run_does_not_execute(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from autocedar.setup_tools import SetupPlan, SetupStep

    plan = SetupPlan([
        SetupStep("Cedar CLI", "INSTALL", "missing", ["cargo", "install", "cedar-policy-cli"]),
    ])
    monkeypatch.setattr("autocedar.setup_tools.build_setup_plan", lambda **kwargs: plan)

    def fail_run_setup_plan(*args: object, **kwargs: object) -> object:
        raise AssertionError("setup should not execute during dry run")

    monkeypatch.setattr("autocedar.setup_tools.run_setup_plan", fail_run_setup_plan)

    rc = cli._cmd_setup(
        argparse.Namespace(
            yes=False,
            dry_run=True,
            skip_cedar=False,
            skip_cvc5=False,
        ),
    )

    assert rc == 0
    assert "autocedar setup --yes" in capsys.readouterr().out


def test_setup_yes_executes_plan(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from autocedar.setup_tools import SetupPlan, SetupStep

    plan = SetupPlan([
        SetupStep("Cedar CLI", "INSTALL", "missing", ["cargo", "install", "cedar-policy-cli"]),
    ])
    result = [SetupStep("Cedar CLI", "OK", "installed")]
    monkeypatch.setattr("autocedar.setup_tools.build_setup_plan", lambda **kwargs: plan)
    monkeypatch.setattr("autocedar.setup_tools.run_setup_plan", lambda plan: result)

    rc = cli._cmd_setup(
        argparse.Namespace(
            yes=True,
            dry_run=False,
            skip_cedar=False,
            skip_cvc5=False,
        ),
    )

    assert rc == 0
    assert "setup commands finished" in capsys.readouterr().out


def test_apikey_command_writes_env_file(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("AUTOCEDAR_CONFIG_DIR", str(tmp_path / "config"))
    validated: list[tuple[str, str]] = []
    monkeypatch.setattr(
        cli,
        "validate_anthropic_api_key",
        lambda value, *, model: validated.append((value, model)),
    )

    rc = cli._cmd_apikey(
        argparse.Namespace(
            key="sk-ant-test123",
            env=None,
            clear=False,
            no_validate=False,
        ),
    )

    env_path = tmp_path / "config" / ".env"
    assert rc == 0
    assert validated == [("sk-ant-test123", cli.default_model_for_provider("anthropic"))]
    assert env_path.read_text() == "ANTHROPIC_API_KEY=sk-ant-test123\n"
    assert "sk-ant-test123" not in capsys.readouterr().out


def test_apikey_command_replaces_existing_user_config_value(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("AUTOCEDAR_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setattr(cli, "validate_anthropic_api_key", lambda value, *, model: None)
    env_path = tmp_path / "config" / ".env"
    env_path.parent.mkdir(parents=True)
    env_path.write_text("ANTHROPIC_API_KEY=sk-ant-...\nAUTOCEDAR_EFFORT=high\n")

    cli._cmd_apikey(
        argparse.Namespace(
            key="sk-ant-realvalue",
            env=None,
            clear=False,
            no_validate=False,
        ),
    )

    assert env_path.read_text() == "ANTHROPIC_API_KEY=sk-ant-realvalue\nAUTOCEDAR_EFFORT=high\n"


def test_apikey_command_still_supports_explicit_env_file(tmp_path: Path) -> None:
    env_path = tmp_path / ".env"

    cli._cmd_apikey(
        argparse.Namespace(
            key="sk-ant-realvalue",
            env=env_path,
            clear=False,
            no_validate=True,
        ),
    )

    assert env_path.read_text() == "ANTHROPIC_API_KEY=sk-ant-realvalue\n"


def test_apikey_command_rejects_placeholder(tmp_path: Path) -> None:
    with pytest.raises(SystemExit):
        cli._cmd_apikey(
            argparse.Namespace(
                key="sk-ant-...",
                env=tmp_path / ".env",
                clear=False,
                no_validate=False,
            ),
        )


def test_apikey_command_does_not_save_when_live_validation_fails(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("AUTOCEDAR_CONFIG_DIR", str(tmp_path / "config"))

    class AuthenticationError(Exception):
        pass

    def fail_validation(value: str, *, model: str) -> None:
        _ = value, model
        raise AuthenticationError("invalid x-api-key")

    monkeypatch.setattr(cli, "validate_anthropic_api_key", fail_validation)

    with pytest.raises(SystemExit) as exc:
        cli._cmd_apikey(
            argparse.Namespace(
                key="sk-ant-invalid123",
                env=None,
                clear=False,
                no_validate=False,
            ),
        )

    assert "did not save" in str(exc.value)
    assert not (tmp_path / "config" / ".env").exists()


def test_parser_exposes_apikey_command() -> None:
    parser = cli._build_parser()
    args = parser.parse_args(["api-key", "sk-ant-test123", "--env", "local.env"])

    assert args.key == "sk-ant-test123"
    assert args.env == Path("local.env")
    assert args.func is cli._cmd_apikey
