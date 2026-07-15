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


def test_jarvis_bundle_has_no_personal_paths() -> None:
    for path in JARVIS.rglob("*"):
        if path.is_file():
            text = path.read_text(errors="replace")
            assert "/Users/" not in text
            assert "Saachi" not in text
