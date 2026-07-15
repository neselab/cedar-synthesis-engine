from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
JARVIS = ROOT / "autocedar-jarvis"


def test_jarvis_shell_files_parse() -> None:
    scripts = sorted((JARVIS / "scripts").glob("*.sh"))
    scripts.extend(sorted((JARVIS / "slurm").glob("*.sbatch")))
    assert scripts
    for script in scripts:
        subprocess.run(["bash", "-n", str(script)], check=True)


def test_jarvis_example_settings_match_default_launcher_values() -> None:
    env_text = (JARVIS / "config" / "jarvis.env.example").read_text()
    values = dict(
        re.findall(r'^([A-Z][A-Z0-9_]*)="([^"]*)"$', env_text, re.MULTILINE)
    )
    settings = json.loads(
        (JARVIS / "config" / "settings.local.json.example").read_text()
    )

    local = settings["providers"]["local"]
    assert local["model"] == values["AUTOCEDAR_MODEL_NAME"]
    assert local["base_url"] == (
        f'http://127.0.0.1:{values["AUTOCEDAR_MODEL_PORT"]}/v1'
    )


def test_jarvis_readiness_key_is_not_passed_in_curl_argv() -> None:
    launcher = (JARVIS / "scripts" / "run-on-node.sh").read_text()
    assert '-H "Authorization: Bearer $LOCAL_API_KEY"' not in launcher
    assert 'curl -fsS --config - "$LOCAL_BASE_URL/models"' in launcher


def test_jarvis_installs_qwen_compatible_vllm_version() -> None:
    installer = (JARVIS / "scripts" / "install-vllm-on-node.sh").read_text()
    assert "--upgrade" in installer
    assert '"vllm>=0.19.0"' in installer
    assert '"huggingface-hub>=0.34.0"' in installer
    assert '"jinja2>=3.1.0"' in installer
    assert 'bin/hf" --version' not in installer


def test_jarvis_launcher_builds_only_typed_model_specific_flags() -> None:
    launcher = (JARVIS / "scripts" / "run-on-node.sh").read_text()
    assert "--language-model-only" in launcher
    assert '--reasoning-parser "$AUTOCEDAR_VLLM_REASONING_PARSER"' in launcher
    assert "--default-chat-template-kwargs" in launcher
    assert '--revision "$AUTOCEDAR_MODEL_REVISION"' in launcher
    assert "AUTOCEDAR_VLLM_EXTRA_ARGS" not in launcher
    assert "--enable-auto-tool-choice" not in launcher
    assert "--tool-call-parser" not in launcher


def test_jarvis_keeps_hugging_face_token_out_of_weight_cache() -> None:
    common = (JARVIS / "scripts" / "_common.sh").read_text()
    launcher = (JARVIS / "scripts" / "run-on-node.sh").read_text()
    assert 'export HF_HOME="$AUTOCEDAR_MODEL_CACHE"' not in launcher
    assert 'export HF_HOME="$AUTOCEDAR_HF_HOME"' in common
    assert 'export HF_TOKEN_PATH="$AUTOCEDAR_HF_HOME/token"' in common
    assert 'export HF_HUB_CACHE="$AUTOCEDAR_MODEL_CACHE/hub"' in common
    assert 'export HF_XET_CACHE="$AUTOCEDAR_MODEL_CACHE/xet"' in common


def test_jarvis_prepares_model_on_cpu_without_token_argument() -> None:
    wrapper = (JARVIS / "scripts" / "prepare-model.sh").read_text()
    helper = (JARVIS / "scripts" / "prepare-model-on-node.sh").read_text()
    assert "build_cpu_slurm_args" in wrapper
    assert "HF_DOWNLOAD_ARGS" in helper
    assert "AutoTokenizer.from_pretrained" in helper
    assert "apply_chat_template" in helper
    assert "Resolved Hugging Face revision:" in helper
    assert "--token" not in helper


def test_jarvis_smoke_invokes_generation_helper_without_key_argument() -> None:
    launcher = (JARVIS / "scripts" / "run-on-node.sh").read_text()
    batch = (JARVIS / "slurm" / "autocedar-smoke.sbatch").read_text()
    assert '"$VLLM_PYTHON" "$SCRIPT_DIR/model_smoke.py"' in launcher
    assert 'model_smoke.py" "$LOCAL_API_KEY"' not in launcher
    assert "--smoke-test" in batch


def test_jarvis_readme_inventory_covers_shipped_files() -> None:
    guide = (JARVIS / "README.md").read_text()
    tracked = subprocess.run(
        ["git", "ls-files", "--", "autocedar-jarvis"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    shipped = [
        Path(path).relative_to("autocedar-jarvis").as_posix() for path in tracked
    ]
    assert shipped
    for relative_path in shipped:
        assert relative_path in guide


def test_jarvis_placeholder_check_ignores_template_comments() -> None:
    env_text = (JARVIS / "config" / "jarvis.env.example").read_text()
    placeholder_assignment = re.compile(
        r"^[A-Z_][A-Z0-9_]*=.*REPLACE_WITH_", re.MULTILINE
    )
    matches = placeholder_assignment.findall(env_text)
    assert matches
    assert all(not match.startswith("#") for match in matches)


def test_jarvis_guide_has_exact_qwen_starting_profile() -> None:
    guide = (JARVIS / "README.md").read_text()
    expected_lines = (
        'AUTOCEDAR_MODEL_REPO="Qwen/Qwen3.6-27B-FP8"',
        'AUTOCEDAR_MODEL_NAME="autocedar-local"',
        'JARVIS_GPU_COUNT="1"',
        'AUTOCEDAR_MAX_MODEL_LEN="32768"',
        'AUTOCEDAR_VLLM_LANGUAGE_MODEL_ONLY="true"',
        'AUTOCEDAR_VLLM_REASONING_PARSER="qwen3"',
        'AUTOCEDAR_VLLM_ENABLE_THINKING="false"',
        "./scripts/prepare-model.sh config/jarvis.env",
        "./scripts/submit-smoke-test.sh config/jarvis.env",
    )
    for line in expected_lines:
        assert line in guide
    assert "Add token as git credential?" in guide


def test_jarvis_bundle_has_no_personal_paths() -> None:
    for path in JARVIS.rglob("*"):
        if path.is_file():
            text = path.read_text(errors="replace")
            assert "/Users/" not in text
            assert "Saachi" not in text
