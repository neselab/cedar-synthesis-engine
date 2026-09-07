"""Runtime regressions for transport deadlines, token context, and terminal recovery."""

import asyncio
import http.client
import json
import socket
import threading
import time
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from autocedar.codex_auth import _read_response_body
from autocedar.harness_adapter import make_harness_synthesizer
from autocedar.llm import LLMClient, PropertyAtomsResponse, _summarize_property_atom
from autocedar.persistence import write_json
from autocedar.providers.base import ModelUsage
from autocedar.source_doc import compile_source_document, select_property_packet
from autocedar.tui import AutoCedarApp, AuthorOptions
from autocedar.ui.terminal import auto_approve
from tests.test_pipeline import _owner_must_floor


def test_trickling_incomplete_sse_line_obeys_wall_deadline():
    receiver, sender = socket.socketpair()
    receiver.settimeout(1)
    stopped = threading.Event()

    def server():
        try:
            sender.sendall(b"HTTP/1.1 200 OK\r\nContent-Type: text/event-stream\r\n\r\ndata: ")
            while not stopped.wait(0.01):
                sender.sendall(b"x")  # Never completes readline; never trips idle timeout.
        except OSError:
            pass

    thread = threading.Thread(target=server, daemon=True)
    thread.start()
    response = http.client.HTTPResponse(receiver)
    try:
        response.begin()
        start = time.monotonic()
        with pytest.raises(TimeoutError):
            _read_response_body(response, timeout=0.15, expects_stream=True)
        assert time.monotonic() - start < 0.8
    finally:
        stopped.set()
        response.close()
        receiver.close()
        sender.close()
        thread.join(timeout=1)


def test_property_prompt_keeps_all_encodings_once_and_logs_usage():
    atoms = [replace(_owner_must_floor(), name=f"floor_{i}", symbolic_verified=True,
                     source_excerpt=f"[source_id: src.root.p{i:04d}.l1] " + "Repeated prose. " * 100)
             for i in range(34)]
    calls = []

    class Backend:
        def generate_text(self, **_):
            raise AssertionError("structured call expected")

        def generate_structured(self, **kwargs):
            calls.append(kwargs)
            return SimpleNamespace(parsed=PropertyAtomsResponse(atoms=[]),
                                   usage=ModelUsage(input_tokens=100, output_tokens=10))

    usage = []
    llm = LLMClient(backend=Backend(), provider="codex", usage_callback=usage.append)
    doc = compile_source_document("Owners can read their own resources.")
    packet = select_property_packet(doc, doc.nodes[0], approved_property_atoms=atoms,
                                    prior_decisions=[auto_approve(a) for a in atoms])
    llm.propose_property_atoms(packet.to_prompt_text(include_review_context=False), "schema",
                              prior_atoms=atoms, prior_decisions=[auto_approve(a) for a in atoms])
    prompt = calls[0]["messages"][0].content
    for atom in atoms:
        assert prompt.count(f'"name":"{atom.name}"') == 1
    assert "Repeated prose." not in prompt
    assert prompt.count('"reference_cedar"') == 34
    assert '"atom_name"' not in prompt  # Successful approval is already represented by approved atoms.
    assert len(prompt) < sum(len(json.dumps(a.__dict__, default=str)) for a in atoms) / 2
    assert usage[0]["input_tokens"] == 100
    assert usage[0]["effort"] == "low"


def test_property_summary_preserves_sugar_semantics():
    atom = replace(_owner_must_floor(), constraint_type="disjointness",
                   disjoint_with="blocked", disjoint_target_body="principal.isAdmin")
    assert _summarize_property_atom(atom)["disjoint_target_body"] == "principal.isAdmin"


def test_synthesis_progress_visible_before_run_returns(monkeypatch, tmp_path):
    import autocedar.harness.eval_harness as harness
    messages = []

    def run(**kwargs):
        assert kwargs["fixed_target"] is True
        print("iteration one")
        assert messages == ["iteration one"]
        raise RuntimeError("simulated synthesis interruption")

    monkeypatch.setattr(harness, "run_scenario", run)
    with pytest.raises(RuntimeError, match="interruption"):
        make_harness_synthesizer(output_callback=messages.append)(tmp_path / "scenario")


def test_tui_author_reuses_matching_saved_session_and_resume_command(monkeypatch, tmp_path):
    async def run():
        monkeypatch.chdir(tmp_path)
        app = AutoCedarApp()
        spec = tmp_path / "spec.md"
        spec.write_text("Users can read.")
        previous = tmp_path / "autocedar-runs" / "old"
        (previous / "input").mkdir(parents=True)
        (previous / "input" / "spec.md").write_text(spec.read_text())
        (previous / "stage1").mkdir()
        (previous / "stage1" / "final_schema.cedarschema").write_text("entity User;")
        calls = []
        app._start_task = lambda _name, function: function()
        app._author = calls.append
        async with app.run_test() as pilot:
            app._start_author(AuthorOptions(spec=spec))
            assert calls[0].resume_from.resolve() == previous
            assert calls[0].session_id != "old"
            app.latest_session_dir = previous
            app._execute_agent_action(app._agent_action_from_command("resume", []))
            assert calls[-1].resume_from == previous
            await pilot.exit(None)

    asyncio.run(run())


def test_tui_busy_save_reports_autosaved_session_without_new_work():
    async def run():
        app = AutoCedarApp()
        async with app.run_test() as pilot:
            app.busy = True
            app.latest_session_dir = Path("runs/keep")
            app.property_progress_summary = "source 18/33"
            app._handle_busy_input("/save")
            assert "runs/keep" in app.last_assistant_text
            assert "source 18/33" in app.last_assistant_text
            assert app.pending_action is None
            await pilot.exit(None)

    asyncio.run(run())


def test_failed_structured_call_records_unknown_tokens_not_zero():
    class Backend:
        def generate_text(self, **_):
            pass

        def generate_structured(self, **_):
            raise TimeoutError("timeout")

    events = []
    llm = LLMClient(backend=Backend(), usage_callback=events.append)
    with pytest.raises(TimeoutError):
        llm.propose_property_atoms("spec", "schema")
    assert events[0]["success"] is False
    assert events[0]["input_tokens"] is None


def test_fixed_target_never_repairs_invalid_reviewed_reference(tmp_path):
    from autocedar.harness.eval_harness import run_scenario
    from tests.test_pipeline import MINIMAL_SCHEMA, _HAVE_SOLVERS
    if not _HAVE_SOLVERS:
        pytest.skip("Cedar/CVC5 unavailable")
    scenario = tmp_path / "scenario"
    scenario.mkdir()
    (scenario / "schema.cedarschema").write_text(MINIMAL_SCHEMA)
    (scenario / "policy_spec.md").write_text("Owners can read their own resources.")
    (scenario / "references").mkdir()
    reference = scenario / "references" / "broken.cedar"
    bad = 'permit(principal, action, resource) when { principal.nonexistent };'
    reference.write_text(bad)
    (scenario / "verification_plan.py").write_text(
        f"def get_checks():\n    return [dict(name='safety', description='Safety', type='implies', reference_path={str(reference)!r})]\n")

    class NoModelCalls:
        provider_id = "test"

        def generate_text(self, **_):
            pytest.fail("A fixed target must not be repaired by an LLM")

    result = run_scenario(str(scenario), str(tmp_path / "runs"), "test", "test", 1,
                          gen_references=False, no_review=True, backend=NoModelCalls(), fixed_target=True)
    assert not result.converged
    assert "return to HITL target repair" in result.error
    assert reference.read_text() == bad


def test_generated_plan_handles_multiline_summaries_and_quoted_names(tmp_path):
    from autocedar.atoms import VerificationPlanDraft
    from autocedar.property_elicitor import compile_plan
    atom = replace(_owner_must_floor(), name='owner"quoted', plain_english_summary='Line one\nLine "two"')
    compiled = compile_plan(VerificationPlanDraft(properties=[atom]))
    namespace = {"__file__": str(tmp_path / "verification_plan.py")}
    exec(compiled.verification_plan_py, namespace)
    check = namespace["get_checks"]()[0]
    assert check["name"] == atom.name
    assert check["description"] == atom.plain_english_summary
    assert Path(check["floor_path"]).name == atom.name + ".cedar"


def test_ceiling_patcher_ignores_braces_and_when_in_strings_and_comments():
    from autocedar.property_elicitor import wrap_when_with_conjuncts
    original = '// when { bogus\npermit(principal, action, resource) when { resource.label == "}" };'
    patched = wrap_when_with_conjuncts(original, ["context.ok"])
    assert '// when { bogus\npermit' in patched
    assert '(resource.label == "}")' in patched
    assert '&& context.ok' in patched
