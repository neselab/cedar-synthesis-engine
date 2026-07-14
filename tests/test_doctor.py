from __future__ import annotations

import os
from pathlib import Path

import pytest

import autocedar.doctor as doctor


def test_doctor_reports_ready_toolchain(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    cedar = tmp_path / "cedar"
    cvc5 = tmp_path / "cvc5"
    cedar.write_text("#!/bin/sh\n")
    cvc5.write_text("#!/bin/sh\n")
    cedar.chmod(0o755)
    cvc5.chmod(0o755)

    monkeypatch.setattr(doctor, "CEDAR_PATH", str(cedar))
    monkeypatch.setattr(doctor, "CVC5_PATH", str(cvc5))
    monkeypatch.setenv("AUTOCEDAR_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")

    def fake_run_text(cmd: list[str], timeout: int = 10) -> doctor._RunResult:
        _ = timeout
        if cmd[:2] == [str(cedar), "--version"]:
            return doctor._RunResult(0, "cedar-policy-cli 4.10.0")
        if cmd[:3] == [str(cedar), "symcc", "--help"]:
            return doctor._RunResult(
                0,
                "Usage: cedar symcc --principal-type P --action A "
                "--resource-type R --schema S",
            )
        if cmd[:2] == [str(cvc5), "--version"]:
            return doctor._RunResult(0, "This is cvc5 version 1.3.5")
        raise AssertionError(f"unexpected command: {cmd}")

    monkeypatch.setattr(doctor, "_run_text", fake_run_text)
    monkeypatch.setattr(doctor, "_run_symcc", lambda *args, **kwargs: (True, "VERIFIED"))

    report = doctor.run_doctor(cwd=tmp_path)
    text = doctor.format_doctor_report(report)

    assert report.failed is False
    assert "[OK] Cedar SymCC interface: analysis flags are present" in text
    assert "[OK] Live SymCC smoke test: identical owner-view policy implies itself" in text
    assert "Result: OK" in text


def test_doctor_fails_when_symcc_analysis_flags_are_missing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    cedar = tmp_path / "cedar"
    cvc5 = tmp_path / "cvc5"
    cedar.write_text("#!/bin/sh\n")
    cvc5.write_text("#!/bin/sh\n")
    cedar.chmod(0o755)
    cvc5.chmod(0o755)

    monkeypatch.setattr(doctor, "CEDAR_PATH", str(cedar))
    monkeypatch.setattr(doctor, "CVC5_PATH", str(cvc5))

    def fake_run_text(cmd: list[str], timeout: int = 10) -> doctor._RunResult:
        _ = timeout
        if cmd[:2] == [str(cedar), "--version"]:
            return doctor._RunResult(0, "cedar-policy-cli 4.10.0")
        if cmd[:3] == [str(cedar), "symcc", "--help"]:
            return doctor._RunResult(0, "Usage: cedar symcc [OPTIONS]")
        if cmd[:2] == [str(cvc5), "--version"]:
            return doctor._RunResult(0, "This is cvc5 version 1.3.5")
        raise AssertionError(f"unexpected command: {cmd}")

    monkeypatch.setattr(doctor, "_run_text", fake_run_text)

    report = doctor.run_doctor(live_symcc=False, cwd=tmp_path)
    text = doctor.format_doctor_report(report)

    assert report.failed is True
    assert "[FAIL] Cedar SymCC interface:" in text
    assert "--features analyze" in text
    assert "Result: FAIL" in text


def test_doctor_fails_when_live_symcc_smoke_test_fails(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    cedar = tmp_path / "cedar"
    cvc5 = tmp_path / "cvc5"
    cedar.write_text("#!/bin/sh\n")
    cvc5.write_text("#!/bin/sh\n")
    cedar.chmod(0o755)
    cvc5.chmod(0o755)

    monkeypatch.setattr(doctor, "CEDAR_PATH", str(cedar))
    monkeypatch.setattr(doctor, "CVC5_PATH", str(cvc5))

    def fake_run_text(cmd: list[str], timeout: int = 10) -> doctor._RunResult:
        _ = timeout
        if cmd[:2] == [str(cedar), "--version"]:
            return doctor._RunResult(0, "cedar-policy-cli 4.10.0")
        if cmd[:3] == [str(cedar), "symcc", "--help"]:
            return doctor._RunResult(
                0,
                "Usage: cedar symcc --principal-type P --action A "
                "--resource-type R --schema S",
            )
        if cmd[:2] == [str(cvc5), "--version"]:
            return doctor._RunResult(0, "This is cvc5 version 1.3.5")
        raise AssertionError(f"unexpected command: {cmd}")

    monkeypatch.setattr(doctor, "_run_text", fake_run_text)
    monkeypatch.setattr(
        doctor,
        "_run_symcc",
        lambda *args, **kwargs: (False, "Cedar symcc setup error: CVC5 missing"),
    )

    report = doctor.run_doctor(cwd=tmp_path)
    text = doctor.format_doctor_report(report)

    assert report.failed is True
    assert "[FAIL] Live SymCC smoke test:" in text
    assert "CVC5 missing" in text


def test_cvc5_check_uses_actionable_fix_when_missing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    missing = tmp_path / "missing-cvc5"
    monkeypatch.setattr(doctor, "CVC5_PATH", str(missing))

    check = doctor._cvc5_check()

    assert check.status == "FAIL"
    assert "not found" in check.detail
    assert "command -v cvc5" in check.fix


def test_doctor_treats_placeholder_api_key_as_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AUTOCEDAR_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-...")

    check = doctor._llm_check()

    assert check.status == "WARN"
    assert "not set" in check.detail
    assert "autocedar apikey" in check.fix


def test_doctor_accepts_reachable_openai_compatible_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AUTOCEDAR_PROVIDER", "local")
    monkeypatch.setenv("AUTOCEDAR_LOCAL_MODEL", "autocedar-local")
    monkeypatch.setattr(
        doctor,
        "openai_runtime_info",
        lambda: type(
            "RuntimeInfo",
            (),
            {
                "available": True,
                "base_url": "http://127.0.0.1:8000/v1",
                "models": ["autocedar-local"],
            },
        )(),
    )

    check = doctor._llm_check()

    assert check.status == "OK"
    assert "autocedar-local" in check.detail


def test_doctor_rejects_unadvertised_openai_compatible_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AUTOCEDAR_PROVIDER", "local")
    monkeypatch.setenv("AUTOCEDAR_LOCAL_MODEL", "wrong-name")
    monkeypatch.setattr(
        doctor,
        "openai_runtime_info",
        lambda: type(
            "RuntimeInfo",
            (),
            {
                "available": True,
                "base_url": "http://127.0.0.1:8000/v1",
                "models": ["autocedar-local"],
            },
        )(),
    )

    check = doctor._llm_check()

    assert check.status == "FAIL"
    assert "not advertised" in check.detail
    assert "--served-model-name" in check.fix


def test_doctor_reports_unknown_provider_cleanly(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AUTOCEDAR_PROVIDER", "typo")

    check = doctor._llm_check()

    assert check.status == "FAIL"
    assert "unsupported AUTOCEDAR_PROVIDER" in check.detail
    assert "codex, anthropic, or local" in check.fix
