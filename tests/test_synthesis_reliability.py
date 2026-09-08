"""Real-verifier and fault-injection tests; no simulated semantic HITL review."""
import json
import os
import subprocess
from itertools import cycle
from pathlib import Path

import pytest

from autocedar.harness import eval_harness as harness, solver_wrapper as solver
from autocedar.providers import TextResult
from autocedar import grounding


@pytest.mark.parametrize('module', [solver, grounding])
@pytest.mark.parametrize('fault', ['timeout', 'missing', 'empty', 'unknown'])
def test_missing_formal_verdict_is_never_a_counterexample(monkeypatch, module, fault):
    def run(*args, **kwargs):
        if fault == 'timeout':
            raise subprocess.TimeoutExpired('cedar', 30)
        if fault == 'missing':
            raise FileNotFoundError('cedar')
        return subprocess.CompletedProcess(args[0], 0, '' if fault == 'empty' else 'solver returned unknown', '')
    monkeypatch.setattr(module.subprocess, 'run', run)
    passed, output = module._run_symcc('schema', 'User', 'Action::"read"', 'Resource', 'always-denies', [])
    assert not passed
    assert module._is_symcc_tool_error(output)
    if module is solver:
        live = solver.run_always_denies_check('schema', 'candidate', 'User', 'Action::"read"', 'Resource', 'live', 'live', False)
        overlap = solver.run_liveness_overlap_check('schema', 'candidate', 'probe', 'User', 'Action::"read"', 'Resource', 'slice', 'slice')
        assert not live.passed and live.tool_error
        assert not overlap.passed and overlap.tool_error


@pytest.fixture
def scenario(tmp_path):
    root = tmp_path / 'scenario'
    root.mkdir()
    (root / 'schema.cedarschema').write_text('entity User; entity Doc { owner: User }; action read appliesTo { principal: User, resource: Doc };')
    (root / 'policy_spec.md').write_text('Users can read exactly the documents they own.')
    (root / 'references').mkdir()
    (root / 'references' / 'owner.cedar').write_text('permit(principal is User, action == Action::"read", resource is Doc) when { principal == resource.owner };')
    (root / 'verification_plan.py').write_text('''import os
REF = os.path.join(os.path.dirname(__file__), 'references', 'owner.cedar')
def get_checks():
    base = dict(principal_type='User', resource_type='Doc', action='Action::"read"', description='Owner access')
    return [dict(base, name='ceiling', type='implies', reference_path=REF), dict(base, name='floor', type='floor', floor_path=REF)]
''')
    return root


requires_cedar = pytest.mark.skipif(not (os.path.isfile(solver.CEDAR_PATH) and os.path.isfile(solver.CVC5_PATH)), reason='Cedar/CVC5 not available')


class Backend:
    provider_id = 'codex'
    def __init__(self, candidates):
        self.candidates = iter(candidates)
        self.calls = []
    def generate_text(self, **kwargs):
        self.calls.append(list(kwargs['messages']))
        return TextResult(next(self.candidates))


def run(scenario, backend, max_iters=12):
    return harness.run_scenario(str(scenario), str(scenario.parent / 'runs'), 'test', 'test', max_iters,
                                False, no_review=True, backend=backend, fixed_target=True)


@requires_cedar
def test_alternating_failed_candidates_stop_and_keep_diagnostics(scenario, monkeypatch):
    backend = Backend(cycle(['permit(principal, action, resource);', '// deny all']))
    verifications = []
    original = harness.run_verification
    def verify(path):
        verifications.append(path)
        return original(path)
    monkeypatch.setattr(harness, 'run_verification', verify)
    result = run(scenario, backend)
    assert not result.converged and result.iterations == 5
    assert 'three consecutive' in result.error
    assert len(verifications) == 2
    assert max(map(len, backend.calls)) <= 5
    assert result.iteration_log[-1]['status'] == 'stalled'
    output = scenario.parent / 'runs' / 'scenario'
    saved = json.loads((output / 'iterations/iter_5/verification.json').read_text())
    assert saved['reused_verification'] is True
    assert (output / 'iterations/iter_1/candidate.cedar').is_file()
    assert (output / 'iterations/iter_5/feedback.md').is_file()
    assert json.loads((output / 'eval_log.json').read_text())['error'] == result.error
    assert (output / 'references/owner.cedar').read_text() == (scenario / 'references/owner.cedar').read_text()


@requires_cedar
def test_one_repeat_can_recover_without_changing_target(scenario):
    good = (scenario / 'references/owner.cedar').read_text()
    result = run(scenario, Backend(['//deny', '//deny', good]))
    assert result.converged and result.iterations == 3 and not result.error


@requires_cedar
def test_verifier_failure_stops_model_retries(scenario, monkeypatch):
    backend = Backend(cycle(['// deny']))
    monkeypatch.setattr(harness, 'run_verification', lambda _: solver.VerificationResult(1, [
        solver.CheckResult('ceiling', 'implies', '', False, 'solver timed out', tool_error=True)]))
    result = run(scenario, backend)
    assert len(backend.calls) == 1 and not result.converged
    assert 'solver timed out' in result.error
    assert result.iteration_log[-1]['status'] == 'verifier_error'


@requires_cedar
def test_model_failure_preserves_actual_error(scenario):
    class FailingBackend(Backend):
        def generate_text(self, **kwargs):
            raise TimeoutError('provider deadline exceeded')
    result = run(scenario, FailingBackend([]))
    assert 'provider deadline exceeded' in result.error and not result.converged
    assert (scenario.parent / 'runs/scenario/iterations/iter_1/error.json').is_file()


@pytest.mark.parametrize('checks', ['[]', '[dict(name="x", type="flooor")]', '[dict(name="x", type="floor"), dict(name="x", type="floor")]'])
def test_invalid_check_plan_cannot_silently_pass(tmp_path, checks):
    from autocedar.harness.orchestrator import load_checks
    (tmp_path / 'verification_plan.py').write_text(f'def get_checks():\n    return {checks}\n')
    with pytest.raises(ValueError):
        load_checks(str(tmp_path))


@requires_cedar
def test_unfenced_multiline_cedar_survives_extraction_and_verifies(scenario):
    # The former line-prefix heuristic deleted annotations, then/else and Bool
    # literals, turning this valid model response into a permanent parse loop.
    raw = '''@id("owned")
permit(principal is User, action == Action::"read", resource is Doc)
when {
    if principal == resource.owner
    then
        true
    else
        false
};'''
    assert harness._strip_cedar_fencing(raw) == raw
    result = run(scenario, Backend([raw]))
    assert result.converged


@requires_cedar
def test_repeated_syntax_failure_shows_parser_error_and_stops(scenario, capsys):
    result = run(scenario, Backend(cycle(['permit(principal, action, resource) when { ;'])))
    assert result.iterations == 4 and not result.converged
    output = capsys.readouterr().out
    assert 'SYNTAX ERROR' in output and 'unexpected' in output.lower()
    saved = scenario.parent / 'runs/scenario/iterations/iter_4'
    assert (saved / 'model_response.txt').is_file()
    assert 'syntax' in json.loads((saved / 'verification.json').read_text())['results'][0]['check_name']


def test_missing_validator_stops_before_any_model_request(scenario, monkeypatch):
    monkeypatch.setattr(harness, 'run_syntax_check', lambda *_: (False, 'Cedar CLI not found', 'other'))
    backend = Backend([])
    result = run(scenario, backend)
    assert result.iterations == 0 and not backend.calls
    assert 'Cedar validator could not run' in result.error
    assert (scenario.parent / 'runs/scenario/eval_log.json').is_file()


@pytest.mark.parametrize('module', [solver, grounding])
def test_verdict_is_not_inferred_from_counterexample_contents(monkeypatch, module):
    output = 'Policy set 1 implies policy set 2: DOES NOT HOLD\nCounterexample: {"name": "VERIFIED"}'
    monkeypatch.setattr(module.subprocess, 'run', lambda *a, **k: subprocess.CompletedProcess(a[0], 0, output, ''))
    passed, raw = module._run_symcc('schema', 'User', 'Action::"read"', 'Resource', 'implies', [])
    assert not passed and not module._is_symcc_tool_error(raw)
    assert module._is_symcc_tool_error('Could not produce a counterexample: solver unknown')
