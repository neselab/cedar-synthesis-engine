from __future__ import annotations

import argparse
import os
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


def test_version_parser_does_not_resolve_invalid_provider_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AUTOCEDAR_PROVIDER", "typo")

    args = cli._build_parser().parse_args(["version"])

    assert args.func is cli._cmd_version


def test_author_command_injects_harness_synthesizer(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
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
        candidate_path = tmp_path / "out" / "session" / "candidate.cedar"
        candidate_path.parent.mkdir(parents=True)
        candidate_path.write_text("permit (principal, action, resource);\n")
        return SimpleNamespace(
            session_dir=tmp_path / "out" / "session",
            candidate_path=candidate_path,
            final_user_approved=False,
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
    assert "propose_property_atom" in captured
    assert "repair_property_atom" in captured
    assert "approved:  False" in capsys.readouterr().out


def test_authoring_completion_requires_final_candidate_file(tmp_path: Path) -> None:
    missing = SimpleNamespace(candidate_path=tmp_path / "missing.cedar")
    directory = SimpleNamespace(candidate_path=tmp_path)
    candidate = tmp_path / "candidate.cedar"
    candidate.write_text("permit (principal, action, resource);\n")

    assert cli._authoring_completed(missing) is False
    assert cli._authoring_completed(directory) is False
    assert cli._authoring_completed(SimpleNamespace(candidate_path=candidate)) is True


def test_resume_auto_approve_success_is_not_human_approval(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test123")
    prior_session = tmp_path / "prior-session"
    input_dir = prior_session / "input"
    input_dir.mkdir(parents=True)
    (input_dir / "spec.md").write_text("Owners can read their own resources.")

    monkeypatch.setattr(cli, "LLMClient", lambda **kwargs: object())
    monkeypatch.setattr(cli, "make_harness_synthesizer", lambda **kwargs: object())

    def fake_author_pipeline(**kwargs: object) -> SimpleNamespace:
        candidate_path = tmp_path / "out" / "resumed" / "candidate.cedar"
        candidate_path.parent.mkdir(parents=True)
        candidate_path.write_text("permit (principal, action, resource);\n")
        return SimpleNamespace(
            session_dir=candidate_path.parent,
            candidate_path=candidate_path,
            final_user_approved=False,
            notes=[],
        )

    monkeypatch.setattr(cli, "author_pipeline", fake_author_pipeline)

    rc = cli._cmd_resume(
        argparse.Namespace(
            session=str(prior_session),
            out=str(tmp_path / "out"),
            session_id="resumed",
            model="claude-test",
            effort="high",
            auto_approve=True,
            max_schema_gap_repairs=None,
        ),
    )

    assert rc == 0
    assert "approved:  False" in capsys.readouterr().out


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


def test_apikey_command_writes_private_auth_file(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("AUTOCEDAR_MODEL", "gpt-5.5")
    monkeypatch.setenv("AUTOCEDAR_CHAT_MODEL", "local-coder-model")
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

    auth_path = tmp_path / "config" / "auth.json"
    assert rc == 0
    assert validated == [("sk-ant-test123", cli.ANTHROPIC_API_KEY_VALIDATION_MODEL)]
    assert '"api_key": "sk-ant-test123"' in auth_path.read_text()
    assert auth_path.stat().st_mode & 0o777 == 0o600
    assert "sk-ant-test123" not in capsys.readouterr().out


def test_apikey_command_migrates_without_rewriting_legacy_env(
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

    assert env_path.read_text() == "ANTHROPIC_API_KEY=sk-ant-...\nAUTOCEDAR_EFFORT=high\n"
    assert '"api_key": "sk-ant-realvalue"' in (
        tmp_path / "config" / "auth.json"
    ).read_text()


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


def test_local_provider_does_not_prompt_for_anthropic_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AUTOCEDAR_PROVIDER", "local")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr(
        cli.getpass,
        "getpass",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("local provider must not ask for an Anthropic key"),
        ),
    )

    cli._require_api_key_for_llm_command()


def test_parser_exposes_provider_overrides_for_llm_commands() -> None:
    parser = cli._build_parser()

    author = parser.parse_args([
        "author",
        "spec.md",
        "--out",
        "runs",
        "--provider",
        "openai",
        "--model",
        "gpt-test",
    ])
    resume = parser.parse_args([
        "resume",
        "prior",
        "--out",
        "runs",
        "--provider",
        "claude-cli",
    ])
    synthesize = parser.parse_args([
        "synthesize",
        "scenario",
        "--provider",
        "local",
        "--model",
        "served-model",
    ])

    assert (author.provider, author.model) == ("openai", "gpt-test")
    assert resume.provider == "claude-cli"
    assert (synthesize.provider, synthesize.model) == ("local", "served-model")


def test_config_persists_local_endpoint_without_mutating_environment(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("AUTOCEDAR_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.delenv("AUTOCEDAR_PROVIDER", raising=False)
    monkeypatch.delenv("AUTOCEDAR_LOCAL_BASE_URL", raising=False)

    rc = cli._cmd_config(
        argparse.Namespace(
            provider="local",
            model="jarvis-model",
            effort="high",
            endpoint="http://127.0.0.1:9000/v1",
        ),
    )

    assert rc == 0
    contents = (tmp_path / "config" / "settings.json").read_text()
    assert '"default_provider": "local"' in contents
    assert '"base_url": "http://127.0.0.1:9000/v1"' in contents
    assert '"model": "jarvis-model"' in contents
    assert "AUTOCEDAR_PROVIDER" not in os.environ
    assert "AUTOCEDAR_LOCAL_BASE_URL" not in os.environ


def test_config_without_provider_targets_effective_provider_and_reports_source(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("AUTOCEDAR_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setenv("AUTOCEDAR_PROVIDER", "local")
    for name in (
        "AUTOCEDAR_MODEL",
        "AUTOCEDAR_AUTHOR_MODEL",
        "AUTOCEDAR_CHAT_MODEL",
        "AUTOCEDAR_LOCAL_MODEL",
        "AUTOCEDAR_OPENAI_MODEL",
    ):
        monkeypatch.delenv(name, raising=False)

    rc = cli._cmd_config(
        argparse.Namespace(
            provider=None,
            model="effective-local-model",
            effort=None,
            endpoint=None,
        ),
    )

    assert rc == 0
    contents = (tmp_path / "config" / "settings.json").read_text()
    assert '"local"' in contents
    assert '"model": "effective-local-model"' in contents
    output = capsys.readouterr().out
    assert "provider: local (environment:AUTOCEDAR_PROVIDER)" in output
    assert "provider: local (session)" not in output


def test_auth_login_openai_saves_key_in_auth_json(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("AUTOCEDAR_CONFIG_DIR", str(tmp_path / "config"))

    rc = cli._cmd_auth_login(
        argparse.Namespace(provider="openai", api_key="sk-openai-test-value"),
    )

    assert rc == 0
    auth_path = tmp_path / "config" / "auth.json"
    assert '"openai"' in auth_path.read_text()
    assert '"api_key": "sk-openai-test-value"' in auth_path.read_text()
    assert auth_path.stat().st_mode & 0o777 == 0o600


def test_auth_login_anthropic_normalizes_and_validates_before_saving(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("AUTOCEDAR_CONFIG_DIR", str(tmp_path / "config"))
    validated: list[tuple[str, str]] = []
    monkeypatch.setattr(
        cli,
        "validate_anthropic_api_key",
        lambda value, *, model: validated.append((value, model)),
    )

    rc = cli._cmd_auth_login(
        argparse.Namespace(
            provider="anthropic",
            api_key='"sk-ant-\u200bsecret 123"',
        ),
    )

    assert rc == 0
    assert validated == [
        ("sk-ant-secret123", cli.ANTHROPIC_API_KEY_VALIDATION_MODEL),
    ]
    assert '"api_key": "sk-ant-secret123"' in (
        tmp_path / "config" / "auth.json"
    ).read_text()


def test_auth_login_claude_uses_cli_without_shell(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[tuple[list[str], dict[str, object]]] = []
    monkeypatch.setattr(cli.shutil, "which", lambda name: f"/usr/bin/{name}")

    def fake_run(command: list[str], **kwargs: object) -> SimpleNamespace:
        captured.append((command, kwargs))
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(cli.subprocess, "run", fake_run)

    rc = cli._cmd_auth_login(argparse.Namespace(provider="claude-cli", api_key=None))

    assert rc == 0
    assert captured == [(["/usr/bin/claude", "auth", "login"], {"check": False})]
