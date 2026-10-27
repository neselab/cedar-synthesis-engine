#!/bin/bash
# Fig. 2 rerun: CedarBench CyberChair spec through the intent-map pipeline with Claude Haiku 4.5.
set -u
WT=/Users/zeitgeist/research/cedar-synthesis-engine-fixes
R=$(cd "$(dirname "$0")" && pwd)
START=$(date -u +%FT%TZ)
( cd $WT && uv run autocedar author "$R/input/policy_spec.md" --schema "$R/input/schema.cedarschema" \
    --out "$R/output" --session-id cyberchair-haiku45 --provider claude-cli --model claude-haiku-4-5 \
    --effort high --model-review --max-schema-gap-repairs 0 ) < /dev/null > "$R/console.log" 2>&1
CODE=$?
python3 - "$R" "$CODE" "$START" "$(git -C $WT rev-parse HEAD)" "$(git -C $WT status --short | grep -v experiments/ | tr '\n' ';')" <<'PY'
import hashlib, json, sys
from datetime import datetime, timezone
from pathlib import Path
R, code, start, commit, dirty = Path(sys.argv[1]), int(sys.argv[2]), sys.argv[3], sys.argv[4], sys.argv[5]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
cand = R / "output" / "cyberchair-haiku45" / "harness_runs" / "scenario" / "candidate.cedar"
rec = {"exit_code": code, "started_at": start, "finished_at": datetime.now(timezone.utc).strftime("%FT%TZ"),
       "code_commit": commit, "uncommitted_changes": dirty, "provider": "claude-cli", "model": "claude-haiku-4-5", "effort": "high",
       "review": "model review (no person)", "schema_fixed": True,
       "spec_sha256": sha(R / "input/policy_spec.md"), "schema_sha256": sha(R / "input/schema.cedarschema"),
       "candidate_exists": cand.is_file()}
(R / "RUN.json").write_text(json.dumps(rec, indent=2) + "\n")
print(json.dumps(rec, indent=2))
PY
