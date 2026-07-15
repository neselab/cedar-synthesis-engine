# AutoCedar on Stevens Jarvis

This folder is the maintained Stevens-specific setup for AutoCedar. It runs a
local model server and AutoCedar together inside one Slurm GPU allocation.
Nothing in this folder sends a prompt to OpenAI or Anthropic.

You do **not** need to understand Slurm or vLLM before starting. Follow the
steps in order and ask the lab administrator for the cluster values listed
below. Older Jarvis quickstart notes explain basic Slurm use but do not set up
an LLM; use this guide for AutoCedar.

## What happens when you run it

```text
one-time CPU job -> download model into your scratch/cache directory

your laptop -> Stevens VPN -> Jarvis login node -> Slurm GPU node
                                                   |-- vLLM model server
                                                   `-- AutoCedar TUI
```

The model server listens on `127.0.0.1`, so AutoCedar and the model stay on the
same assigned node. The launcher creates a temporary random server key, starts
vLLM, waits until it is ready, runs `autocedar doctor`, opens AutoCedar, and
stops vLLM when you exit.

## Ask the lab administrator first

Copy this list into a message to the administrator:

1. What is my Stevens/Jarvis username, and do I have Jarvis and VPN access?
2. Which **GPU partition** and **Slurm account** should I use? Is a QOS needed?
3. Which **CPU partition** should I use for one-time software installation and
   model download?
4. Which CUDA or cuDNN **module name** should I load on the GPU node?
5. May I use `Qwen/Qwen3.6-27B-FP8` on one L40S GPU with a 32,768-token context?
   If not, which vLLM-compatible instruction/chat model and GPU count should I
   use?
6. What absolute scratch/cache directory should hold the model weights? For
   Qwen3.6-27B-FP8, confirm that at least 50 GB is free and within my quota.
7. Is the model already available at a shared filesystem path? If it is gated,
   may I authenticate to Hugging Face from Jarvis?
8. What host-memory and time limit should I request?

The June 2026 lab notes used `gpu-l40s` and
`cudnn9.1-cuda12.2/9.1.1.17`, but those are examples, not promises. Use the
administrator's current answers.

## One-time setup

### 1. Connect

Connect to the Stevens VPN on your laptop, then replace the username below:

```bash
ssh YOUR_STEVENS_USERNAME@jarvis.stevens.edu
```

You should land on a login node. Never start `vllm serve` directly on that
node; the supplied launcher requests a GPU and owns server cleanup.

### 2. Get the maintained Jarvis folder

On Jarvis:

```bash
git clone --depth 1 https://github.com/neselab/cedar-synthesis-engine.git
cd cedar-synthesis-engine/autocedar-jarvis
```

AutoCedar itself will come from PyPI; the GitHub clone supplies the maintained
Jarvis config, Slurm wrappers, and checks.

### 3. Fill in the Jarvis values

```bash
cp config/jarvis.env.example config/jarvis.env
nano config/jarvis.env
```

Replace every value beginning with `REPLACE_WITH_`. Use `none` only where the
comments say it is allowed. In `nano`, save with `Ctrl-O`, press Enter, then
exit with `Ctrl-X`.

`AUTOCEDAR_MODEL_CACHE` must be the absolute scratch/cache path supplied by
the administrator. Leave `AUTOCEDAR_HF_HOME` at its private default under your
home directory. The model weights go into the former; a Hugging Face login
token, if one is ever needed, stays in the latter.

Check that no placeholder remains:

```bash
grep -nE '^[A-Z_][A-Z0-9_]*=.*REPLACE_WITH_' config/jarvis.env
```

No output means no assignment still has a placeholder. `config/jarvis.env` is
ignored by Git. Do not put a Stevens password, API key, or Hugging Face token
in it.

### 4. Configure the LLM

#### Recommended starting model: Qwen3.6-27B-FP8

“Qwen 3.6 27B” is the exact model name. Qwen publishes both the standard
[`Qwen/Qwen3.6-27B`](https://huggingface.co/Qwen/Qwen3.6-27B) checkpoint and an
official [`Qwen/Qwen3.6-27B-FP8`](https://huggingface.co/Qwen/Qwen3.6-27B-FP8)
checkpoint. Use the official FP8 checkpoint for a one-L40S starting profile.

The standard checkpoint's official
[weight index](https://huggingface.co/Qwen/Qwen3.6-27B/blob/main/model.safetensors.index.json)
accounts for more than 51 GiB before vLLM's runtime memory, so it cannot fit
in the 48 GB VRAM of one
[NVIDIA L40S](https://www.nvidia.com/en-us/data-center/l40s/). The FP8
repository is roughly 31 GB. A 32,768-token, text-only FP8 configuration is a
practical starting point on one L40S; the administrator should still confirm
the allocation.

Set these exact lines in `config/jarvis.env`:

```bash
AUTOCEDAR_MODEL_REPO="Qwen/Qwen3.6-27B-FP8"
AUTOCEDAR_MODEL_NAME="autocedar-local"
AUTOCEDAR_MODEL_REVISION="none"
JARVIS_GPU_COUNT="1"
AUTOCEDAR_MAX_MODEL_LEN="32768"
AUTOCEDAR_GPU_MEMORY_UTILIZATION="0.90"
AUTOCEDAR_VLLM_LANGUAGE_MODEL_ONLY="true"
AUTOCEDAR_VLLM_REASONING_PARSER="qwen3"
AUTOCEDAR_VLLM_ENABLE_THINKING="false"
AUTOCEDAR_LOCAL_MAX_TOKENS="8192"
```

The three `AUTOCEDAR_VLLM_*` values matter:

- `LANGUAGE_MODEL_ONLY=true` avoids loading the vision components AutoCedar
  does not use.
- `REASONING_PARSER=qwen3` selects Qwen's official vLLM parser.
- `ENABLE_THINKING=false` keeps Qwen's internal reasoning from consuming the
  output budget before AutoCedar's required JSON result.

Qwen3.6 does not use `/think` or `/nothink` switches. Do not add tool-call
flags: AutoCedar uses JSON-schema structured responses, not model-invoked
tools. These choices follow Qwen's model card and vLLM's
[reasoning configuration](https://docs.vllm.ai/en/v0.19.0/features/reasoning_outputs/).

`JARVIS_GPU_MEMORY="64G"` is CPU-side host RAM requested through Slurm
`--mem`; it is **not** the GPU's VRAM. Raising it will not fix a CUDA
out-of-memory error.

#### Using another local model

Ask the administrator for a model that:

1. is supported by vLLM 0.19 or newer;
2. has a system/user chat template; and
3. can answer OpenAI-compatible `/v1/chat/completions` requests with
   `response_format.type=json_schema`.

For a non-Qwen model, start with the generic values already in the config:

```bash
AUTOCEDAR_VLLM_LANGUAGE_MODEL_ONLY="false"
AUTOCEDAR_VLLM_REASONING_PARSER="none"
AUTOCEDAR_VLLM_ENABLE_THINKING="default"
```

Change them only when that model's official documentation requires it. The
launcher intentionally does not accept a free-form string of extra vLLM
arguments.

### 5. Install `uv` and AutoCedar 0.2

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
uv python install 3.12
uv tool install --upgrade "autocedar>=0.2,<0.3"
autocedar --version
```

Add the PATH line to `~/.bashrc` so future shells can find AutoCedar:

```bash
printf '%s\n' 'export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
```

### 6. Install Cedar, CVC5, and vLLM

Run these from the `autocedar-jarvis` directory on the login node:

```bash
./scripts/install-verifiers.sh config/jarvis.env
./scripts/install-vllm.sh config/jarvis.env
```

The first command uses a CPU job to install Cedar CLI 4.10.0 with symbolic
analysis plus CVC5 1.3.4. The second uses a GPU job to create a separate vLLM
0.19-or-newer environment at the path in your config. Keeping vLLM separate
prevents its CUDA/PyTorch packages from changing AutoCedar's environment.

If either command says the cluster blocks a download or a module is missing,
send the complete error to the lab administrator. Do not guess a replacement
partition, module, or model.

### 7. Download and check the model

The official Qwen3.6 checkpoints are public, so Qwen3.6-27B-FP8 does not need
a Hugging Face account or token. Run:

```bash
./scripts/prepare-model.sh config/jarvis.env
```

This uses a CPU job to download the weights before GPU time is allocated. It
prints disk usage, the resolved snapshot path, and a chat-template check. A
first Qwen download is large and can take a while; later runs reuse the cache.

If the administrator instead approves a gated/private model, authenticate only
after vLLM is installed:

```bash
source config/jarvis.env
umask 077
export HF_HOME="$AUTOCEDAR_HF_HOME"
export HF_TOKEN_PATH="$AUTOCEDAR_HF_HOME/token"
"$AUTOCEDAR_VLLM_ENV/bin/hf" auth login
"$AUTOCEDAR_VLLM_ENV/bin/hf" auth whoami
./scripts/prepare-model.sh config/jarvis.env
```

Paste the token only into the hidden `hf auth login` prompt. If it asks
`Add token as git credential?`, type `n` and press Enter so the token remains
only in the private Hugging Face token file. Never pass it as a command-line
argument or add it to `config/jarvis.env`.

For a reproducible research run, copy the value printed after
`Resolved Hugging Face revision:` into `AUTOCEDAR_MODEL_REVISION`. Leave it as
`none` for ordinary coursework.

### 8. Check that the model can actually answer AutoCedar-style requests

```bash
./scripts/submit-smoke-test.sh config/jarvis.env
squeue -u "$USER"
```

The submit command prints a job ID. After it finishes:

```bash
cat logs/autocedar-smoke-JOB_ID.out
```

The job checks the model listing, verifier setup, one small chat completion,
and one JSON-schema completion. Both generation checks must say `OK`. This is
a backend plumbing check only: it does not prove that a Cedar policy is
correct and it is not human semantic review.

## Every time: launch AutoCedar

From `autocedar-jarvis` on the Jarvis login node:

```bash
./scripts/run-interactive.sh config/jarvis.env
```

That is the only launch command you normally need. Slurm will print the GPU
node name. vLLM's log is saved under `logs/`.

When the TUI opens, the launcher has already selected the local provider and
passed the model name, endpoint, and temporary server key to AutoCedar. Check
the live configuration with:

```text
/settings
/models
```

`/settings` should report provider `local`, the model from
`AUTOCEDAR_MODEL_NAME`, and an endpoint using the port from
`AUTOCEDAR_MODEL_PORT`. `/models` should list that model. Do not type
`/provider`, `/endpoint`, or `/model` during a normal Jarvis launch; those
commands change settings rather than merely displaying them.

To author from a lab-provided specification:

```text
/author /full/path/to/policy_spec.md --out /full/path/to/autocedar-runs
```

Use full paths at first. Press `Ctrl-C` or quit AutoCedar normally when done;
the launcher stops vLLM and releases the Slurm job automatically. Back on the
login node, verify that no job remains:

```bash
squeue -u "$USER"
```

If a forgotten job is still running, stop it with `scancel JOB_ID`.

## Optional: save the local provider as your default

The launcher works without this step. The supplied settings example assumes
the model name is `autocedar-local` and the port is `8000`. Check your actual
values first:

```bash
grep -E '^(AUTOCEDAR_MODEL_NAME|AUTOCEDAR_MODEL_PORT)=' config/jarvis.env
```

If those two values still match the example and this is a new AutoCedar
installation, you may copy it:

```bash
install -d -m 700 "$HOME/.config/autocedar"
install -m 600 config/settings.local.json.example \
  "$HOME/.config/autocedar/settings.json"
```

If `~/.config/autocedar/settings.json` already exists, do not overwrite it.
If the model name or port differs, skip the copy; the normal Jarvis launcher
already passes the correct values. To save custom defaults for use outside the
launcher, use `/provider`, `/endpoint`, and `/model` inside the TUI.

## Your responsibility during human review

AutoCedar pauses on proposed schema atoms and verification-property atoms.
Before approving one, compare:

1. the full natural-language requirement;
2. the proposed atom; and
3. what the Cedar declaration or policy actually means.

Approve only when all three match. Reject or edit an atom that changes,
removes, or invents a requirement. Formal consistency checks cannot decide
human intent. Never use `--auto-approve` for a real policy or research result;
it is only a plumbing-test option.

## Common problems

| Symptom | What to do |
| --- | --- |
| SSH cannot reach Jarvis | Connect to Stevens VPN and retry. |
| Slurm rejects the job | Recheck the partition, account, QOS, host memory, GPU count, and time with the lab administrator. |
| `module` cannot find CUDA/cuDNN | Ask for the current exact module name; do not substitute an old path. |
| Model preparation says `401` or `gated repo` | Qwen3.6-27B-FP8 is public. For a different gated model, run the private `hf auth login` steps above. |
| Model preparation says quota/disk full | Ask for a larger scratch/cache path. Do not put 31 GB of Qwen weights in a small home directory. |
| The chat-template check fails | The selected model is not ready for chat serving. Confirm the exact instruction/chat checkpoint with the administrator. |
| vLLM exits while loading | Read `logs/vllm-JOB_ID.log`; check the model path/revision, CUDA module, and GPU allocation. |
| GPU out of memory with Qwen FP8 | Change `AUTOCEDAR_MAX_MODEL_LEN` from `32768` to `16384` and retry, or ask for more GPUs. Raising `JARVIS_GPU_MEMORY` only raises host RAM. |
| JSON-schema smoke check fails | Confirm the three Qwen vLLM settings, then rerun `install-vllm.sh` to upgrade vLLM. |
| `autocedar doctor` reports Cedar/CVC5 failure | Rerun `install-verifiers.sh`, then send the full error to the administrator. |
| The model server is unreachable | Start AutoCedar through `run-interactive.sh`; the server and TUI must share one GPU allocation. |

For reproducible experiments, record the model repository and resolved
revision, vLLM version, GPU type/count, context length, and AutoCedar version.
Do not silently switch models during a run.

## What is in this folder

```text
README.md                              this guide
.gitignore                             keeps local config and logs out of Git
config/jarvis.env.example              values to get from the lab administrator
config/settings.local.json.example     optional non-secret AutoCedar settings
scripts/install-verifiers.sh           one-time CPU Slurm verifier setup
scripts/install-verifiers-on-node.sh   internal helper called by the setup script
scripts/install-vllm.sh                one-time GPU Slurm vLLM setup
scripts/install-vllm-on-node.sh        internal helper called by the setup script
scripts/prepare-model.sh               one-time CPU model download/check
scripts/prepare-model-on-node.sh       internal helper called by prepare-model
scripts/run-interactive.sh             normal interactive launcher
scripts/run-on-node.sh                 internal helper called inside the GPU job
scripts/model_smoke.py                 ordinary-chat and JSON-schema plumbing check
scripts/submit-smoke-test.sh           batch wrapper for the model smoke test
scripts/_common.sh                     shared internal launcher functions
slurm/autocedar-smoke.sbatch           batch job used by the smoke-test wrapper
```

Run only the wrapper commands named in the setup and launch steps above. The
`*-on-node.sh`, `run-on-node.sh`, `_common.sh`, `model_smoke.py`, and `.sbatch`
files are called automatically inside Slurm jobs.
