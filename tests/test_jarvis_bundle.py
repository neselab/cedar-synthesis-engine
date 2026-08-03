from __future__ import annotations

import json
import os
import re
import shutil
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
    assert '"ninja>=1.11.0"' in installer
    assert 'bin/hf" --version' not in installer


def test_jarvis_avoids_flashinfer_sampler_cuda_jit() -> None:
    common = (JARVIS / "scripts" / "_common.sh").read_text()
    installer = (JARVIS / "scripts" / "install-vllm-on-node.sh").read_text()
    launcher = (JARVIS / "scripts" / "run-on-node.sh").read_text()

    disable = 'export VLLM_USE_FLASHINFER_SAMPLER="0"'
    launch = '"${VLLM_COMMAND[@]}" >"$VLLM_LOG" 2>&1 &'
    assert disable in launcher
    assert launcher.index(disable) < launcher.index(launch)
    for script in (common, installer, launcher):
        assert "NVCC_PREPEND_FLAGS" not in script
        assert "-allow-unsupported-compiler" not in script
        assert "configure_cuda_122_host_compiler" not in script


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


def test_jarvis_example_is_ready_to_copy_without_placeholders() -> None:
    env_text = (JARVIS / "config" / "jarvis.env.example").read_text()
    placeholder_assignment = re.compile(
        r"^[A-Z_][A-Z0-9_]*=.*REPLACE_WITH_", re.MULTILINE
    )
    matches = placeholder_assignment.findall(env_text)
    assert not matches


def test_jarvis_example_uses_documented_defaults() -> None:
    env_text = (JARVIS / "config" / "jarvis.env.example").read_text()
    expected_lines = (
        'JARVIS_GPU_PARTITION="gpu-l40s"',
        'JARVIS_CPU_PARTITION="compute"',
        'JARVIS_SLURM_ACCOUNT="none"',
        'JARVIS_SLURM_QOS="none"',
        'JARVIS_CUDA_MODULE="cudnn9.1-cuda12.2/9.1.1.17"',
        'AUTOCEDAR_MODEL_REPO="Qwen/Qwen3.6-27B-FP8"',
        'AUTOCEDAR_MODEL_CACHE="${SCRATCH:-$HOME/.cache}/autocedar/models"',
        'AUTOCEDAR_VLLM_LANGUAGE_MODEL_ONLY="true"',
        'AUTOCEDAR_VLLM_REASONING_PARSER="qwen3"',
        'AUTOCEDAR_VLLM_ENABLE_THINKING="false"',
    )
    for line in expected_lines:
        assert line in env_text


def test_jarvis_preflight_checks_requests_without_allocating() -> None:
    preflight = (JARVIS / "scripts" / "preflight.sh").read_text()
    assert preflight.count("--test-only") == 2
    assert "build_cpu_slurm_args" in preflight
    assert "build_gpu_slurm_args" in preflight
    assert "AVAILABLE_KIB" in preflight
    assert "50 GiB" in preflight
    assert "PASS:" in preflight


def test_jarvis_preflight_omits_account_and_qos(tmp_path: Path) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    slurm_log = tmp_path / "srun.log"

    fake_commands = {
        "sinfo": '#!/bin/sh\nprintf "partition available\\n"\n',
        "srun": (
            '#!/bin/sh\nprintf "%s\\n" "$*" >> "$SLURM_LOG"\n'
            'printf "Job would start immediately\\n"\n'
        ),
        "df": (
            '#!/bin/sh\n'
            'if [ "$1" = "-Pk" ]; then\n'
            '  printf "Filesystem 1024-blocks Used Available Capacity Mounted\\n"\n'
            '  printf "fake 104857600 1 104857599 1%% /fake\\n"\n'
            "else\n"
            '  printf "fake 100G 1K 100G 1%% /fake\\n"\n'
            "fi\n"
        ),
    }
    for name, contents in fake_commands.items():
        path = fake_bin / name
        path.write_text(contents)
        path.chmod(0o755)

    config = tmp_path / "jarvis.env"
    config.write_text(
        "\n".join(
            (
                'JARVIS_GPU_PARTITION="gpu-l40s"',
                'JARVIS_CPU_PARTITION="compute"',
                'JARVIS_SLURM_ACCOUNT="none"',
                'JARVIS_SLURM_QOS="none"',
                'JARVIS_CUDA_MODULE="none"',
                f'AUTOCEDAR_MODEL_CACHE="{tmp_path / "model-cache"}"',
                f'AUTOCEDAR_HF_HOME="{tmp_path / "hf-home"}"',
                'JARVIS_GPU_COUNT="1"',
                'JARVIS_GPU_CPUS="2"',
                'JARVIS_GPU_MEMORY="64G"',
                'JARVIS_GPU_TIME="04:00:00"',
                'JARVIS_CPU_CPUS="4"',
                'JARVIS_CPU_MEMORY="16G"',
                'JARVIS_CPU_TIME="02:00:00"',
            )
        )
        + "\n"
    )

    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}:{env['PATH']}"
    env["SLURM_LOG"] = str(slurm_log)
    result = subprocess.run(
        [str(JARVIS / "scripts" / "preflight.sh"), str(config)],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )

    requests = slurm_log.read_text()
    assert requests.count("--test-only") == 2
    assert "--partition=compute" in requests
    assert "--partition=gpu-l40s" in requests
    assert "--account" not in requests
    assert "--qos" not in requests
    assert "PASS:" in result.stdout


def test_jarvis_wrappers_work_from_a_fresh_user_home(tmp_path: Path) -> None:
    bundle = tmp_path / "autocedar-jarvis"
    shutil.copytree(
        JARVIS,
        bundle,
        ignore=shutil.ignore_patterns("__pycache__", "logs", "jarvis.env"),
    )
    config = bundle / "config" / "jarvis.env"
    shutil.copy2(bundle / "config" / "jarvis.env.example", config)

    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    slurm_log = tmp_path / "slurm.log"
    fake_slurm = (
        "#!/bin/sh\n"
        'printf "%s %s\\n" "$(basename "$0")" "$*" >> "$SLURM_LOG"\n'
        'if [ "$(basename "$0")" = "sbatch" ]; then\n'
        '  printf "Submitted batch job 12345\\n"\n'
        "fi\n"
    )
    for name in ("srun", "sbatch"):
        path = fake_bin / name
        path.write_text(fake_slurm)
        path.chmod(0o755)

    student_home = tmp_path / "student-home"
    student_scratch = tmp_path / "student-scratch"
    student_home.mkdir()
    student_scratch.mkdir()
    env = os.environ.copy()
    env["HOME"] = str(student_home)
    env["SCRATCH"] = str(student_scratch)
    env["PATH"] = f"{fake_bin}:{env['PATH']}"
    env["SLURM_LOG"] = str(slurm_log)

    wrappers = (
        "install-verifiers.sh",
        "install-vllm.sh",
        "prepare-model.sh",
        "run-interactive.sh",
        "submit-smoke-test.sh",
    )
    for wrapper in wrappers:
        subprocess.run(
            [str(bundle / "scripts" / wrapper), str(config)],
            check=True,
            capture_output=True,
            text=True,
            env=env,
        )

    requests = slurm_log.read_text()
    assert requests.count("\n") == len(wrappers)
    assert requests.count("--partition=compute") == 2
    assert requests.count("--partition=gpu-l40s") == 3
    assert "--pty" in requests
    assert "--account" not in requests
    assert "--qos" not in requests
    assert "/Users/" not in requests
    assert "jarvis-password" not in requests


def test_jarvis_guide_has_exact_qwen_starting_profile() -> None:
    guide = (JARVIS / "README.md").read_text()
    env_text = (JARVIS / "config" / "jarvis.env.example").read_text()
    expected_config_lines = (
        'AUTOCEDAR_MODEL_REPO="Qwen/Qwen3.6-27B-FP8"',
        'AUTOCEDAR_MODEL_NAME="autocedar-local"',
        'JARVIS_GPU_COUNT="1"',
        'AUTOCEDAR_MAX_MODEL_LEN="32768"',
        'AUTOCEDAR_VLLM_LANGUAGE_MODEL_ONLY="true"',
        'AUTOCEDAR_VLLM_REASONING_PARSER="qwen3"',
        'AUTOCEDAR_VLLM_ENABLE_THINKING="false"',
    )
    for line in expected_config_lines:
        assert line in env_text

    expected_guide_lines = (
        "./scripts/prepare-model.sh config/jarvis.env",
        "./scripts/submit-smoke-test.sh config/jarvis.env",
        "./scripts/preflight.sh config/jarvis.env",
    )
    for line in expected_guide_lines:
        assert line in guide


def test_jarvis_bundle_has_no_personal_paths() -> None:
    for path in JARVIS.rglob("*"):
        if path.is_file() and "__pycache__" not in path.parts:
            text = path.read_text(errors="replace")
            assert "/Users/" not in text
            assert "Saachi" not in text


def test_jarvis_guide_requires_portable_full_ssh_command() -> None:
    guide = (JARVIS / "README.md").read_text()
    full_command = "ssh YOUR_STEVENS_USERNAME@jarvis.stevens.edu"
    assert guide.count(full_command) >= 3
    assert "\njarvis\n" not in guide
    assert "\nssh jarvis\n" not in guide
    assert "Host jarvis" not in guide
    assert "id_ed25519" not in guide


def test_jarvis_guide_hands_off_to_current_interactive_agent() -> None:
    guide = (JARVIS / "README.md").read_text()
    assert "../README.md#interactive-agent-usage" in guide
    assert "start a policy draft" in guide
    assert "show the draft" in guide
    assert "author this" in guide
    assert "Nothing after this point is Jarvis-specific." in guide
    assert "AutoCedar needs a plain-text or Markdown file" not in guide
