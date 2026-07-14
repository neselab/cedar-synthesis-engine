# AutoCedar on Stevens Jarvis

This folder is the Stevens-specific part of AutoCedar. It runs a local model
server and AutoCedar together inside one Slurm GPU allocation. Nothing in this
folder sends a prompt to OpenAI or Anthropic.

You do **not** need to understand Slurm or vLLM before starting. Follow the
steps in order and ask the lab administrator for the values listed below.

## What happens when you run it

```text
your laptop -> Stevens VPN -> Jarvis login node -> Slurm GPU node
                                                   |-- vLLM model server
                                                   `-- AutoCedar TUI
```

The server listens on `127.0.0.1`, so AutoCedar and the model stay on the same
assigned node. The launcher creates a temporary random server key, starts
vLLM, waits until it is ready, runs `autocedar doctor`, opens AutoCedar, and
stops vLLM when you exit.

## Ask the lab administrator first

Copy this list into a message to the administrator:

1. What is my Stevens/Jarvis username, and do I have Jarvis and VPN access?
2. Which **GPU partition** and **Slurm account** should I use? Is a QOS needed?
3. Which **CPU partition** should I use for one-time software compilation?
4. Which CUDA or cuDNN **module name** should I load on the GPU node?
5. Which Hugging Face model repository or shared model path is approved for
   AutoCedar, and how many GPUs does it need?
6. What absolute scratch/cache directory should hold the model weights? Does it
   have enough quota?
7. Is the model already cached? If it is gated, how should I authenticate to
   Hugging Face without putting a token in a script?
8. What memory and time limit should I request?

The June 2026 lab notes used `gpu-l40s` and
`cudnn9.1-cuda12.2/9.1.1.17`, but those are examples, not promises. Use the
administrator's current answers.

## One-time setup

### 1. Connect

Connect to the Stevens VPN on your laptop, then replace the username below:

```bash
ssh YOUR_STEVENS_USERNAME@jarvis.stevens.edu
```

You should land on a login node. Never start vLLM directly on that node.

### 2. Get this folder

On Jarvis:

```bash
git clone --depth 1 https://github.com/neselab/cedar-synthesis-engine.git
cd cedar-synthesis-engine/autocedar-jarvis
```

AutoCedar itself will come from PyPI; the GitHub clone only supplies these
Jarvis templates.

### 3. Fill in the Jarvis values

```bash
cp config/jarvis.env.example config/jarvis.env
nano config/jarvis.env
```

Replace every value beginning with `REPLACE_WITH_`. Use `none` only where the
comments say it is allowed. In `nano`, save with `Ctrl-O`, press Enter, then
exit with `Ctrl-X`.

Check that no placeholder remains:

```bash
grep -n REPLACE_WITH_ config/jarvis.env
```

No output means the file is ready. `config/jarvis.env` is ignored by Git.
Do not put a Stevens password, API key, or Hugging Face token in it.

### 4. Install `uv` and AutoCedar 0.2

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

### 5. Install Cedar, CVC5, and vLLM

Run these from the `autocedar-jarvis` directory on the login node:

```bash
./scripts/install-verifiers.sh config/jarvis.env
./scripts/install-vllm.sh config/jarvis.env
```

The first command uses a CPU job to install Cedar CLI 4.10.0 with symbolic
analysis plus CVC5 1.3.4. The second uses a GPU job to create a separate vLLM
environment at the path in your config. Keeping vLLM separate prevents its
CUDA/PyTorch packages from changing AutoCedar's environment.

If either command says the cluster blocks a download or a module is missing,
send the complete error to the lab administrator. Do not guess a replacement
partition, module, or model.

## Every time: launch AutoCedar

From `autocedar-jarvis` on the Jarvis login node:

```bash
./scripts/run-interactive.sh config/jarvis.env
```

That is the only launch command you normally need. Slurm will print the GPU
node name. The first model download may take several minutes; its log is saved
under `logs/`.

When the TUI opens, these commands show the active local configuration:

```text
/provider local
/endpoint http://127.0.0.1:8000/v1
/model autocedar-local
/models
/settings
```

The launcher already supplies the endpoint and model, so the commands are
mainly useful for learning and checking the configuration. To author from a
lab-provided specification:

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

The launcher works without this step. For a new AutoCedar installation, you
may copy the non-secret settings example:

```bash
install -d -m 700 "$HOME/.config/autocedar"
install -m 600 config/settings.local.json.example \
  "$HOME/.config/autocedar/settings.json"
```

If `~/.config/autocedar/settings.json` already exists, do not overwrite it.
Use `/provider`, `/endpoint`, and `/model` inside the TUI instead.

## Optional: submit a non-interactive smoke test

This checks only the Slurm allocation, model server, and verifier plumbing:

```bash
./scripts/submit-smoke-test.sh config/jarvis.env
squeue -u "$USER"
```

The submit command prints a job ID. After it finishes:

```bash
cat logs/autocedar-smoke-JOB_ID.out
```

A passing smoke test is **not** human review and does not validate a policy's
meaning.

## Your responsibility during human review

AutoCedar pauses on proposed schema and policy atoms. Before approving one,
compare:

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
| Slurm rejects the job | Recheck the partition, account, QOS, memory, GPU count, and time with the lab administrator. |
| `module` cannot find CUDA/cuDNN | Ask for the current exact module name; do not substitute an old path. |
| vLLM exits while loading | Read `logs/vllm-JOB_ID.log`; the usual causes are a wrong model path, gated-model authentication, quota, or GPU memory. |
| GPU out of memory | Ask which model/GPU to use. With approval, lower `AUTOCEDAR_MAX_MODEL_LEN`; record any research-run change. |
| `autocedar doctor` reports Cedar/CVC5 failure | Rerun `install-verifiers.sh`, then send the full error to the administrator. |
| The model server is unreachable | Make sure AutoCedar was started through `run-interactive.sh`; the server and TUI must share one GPU allocation. |

For reproducible experiments, record the model repository, served model name,
vLLM version, GPU type/count, context length, and AutoCedar version. Do not
silently switch models during a run.

## What is in this folder

```text
config/jarvis.env.example          values to get from the lab administrator
config/settings.local.json.example optional non-secret AutoCedar settings
scripts/install-verifiers.sh       one-time CPU Slurm setup
scripts/install-vllm.sh            one-time GPU Slurm setup
scripts/run-interactive.sh         normal interactive launcher
scripts/submit-smoke-test.sh       optional batch plumbing test
slurm/autocedar-smoke.sbatch       batch job used by the smoke-test wrapper
```

The scripts have been syntax-checked locally, but the complete workflow has
not yet been run on Jarvis because Stevens VPN access was unavailable. That is
why cluster-specific values remain explicit placeholders.
