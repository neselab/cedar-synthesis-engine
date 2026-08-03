# AutoCedar on Stevens Jarvis

This guide assumes you have never used Jarvis or Slurm. Start at the top. Copy
each command exactly. Do not skip a numbered step.

You will run AutoCedar with the local `Qwen/Qwen3.6-27B-FP8` model on one
Jarvis L40S GPU. You do not need an OpenAI key or an Anthropic key.

This guide covers the Jarvis setup only. After AutoCedar opens, it works the
same way it does on any other computer. Use the main
[Interactive Agent Usage guide](../README.md#interactive-agent-usage) for the
complete and current AutoCedar instructions.

## Five words used in this guide

- **Jarvis** is Stevens' shared group of powerful computers.
- **Slurm** is the waiting line that gives each person time on those computers.
- A **partition** is a named group of computers in Jarvis. This guide uses
  `compute` for CPU work and `gpu-l40s` for GPU work.
- A **job** is one task sent to Slurm. Slurm gives every job a number.
- **vLLM** is the program that runs Qwen. The scripts start and stop it for
  you.

## Before you start

You need:

1. a Stevens account with Jarvis access;
2. the Stevens VPN on your laptop;
3. about 50 GB of free Jarvis storage; and
4. permission to use the `gpu-l40s` partition.

There is no separate “Slurm ID” to find:

- Your **Jarvis username** is your Stevens login username. After login,
  `whoami` prints it.
- A **job ID** is created automatically every time Slurm accepts a job.
- You do not need to type a **Slurm account name**. The supplied value `none`
  tells the scripts not to add an account name to the job.

The supplied defaults are:

```text
CPU partition: compute
GPU partition: gpu-l40s
Slurm account: none (do not send an --account option)
Slurm QOS: none (do not send a --qos option)
CUDA/cuDNN module: cudnn9.1-cuda12.2/9.1.1.17
Model: Qwen/Qwen3.6-27B-FP8
GPUs: 1
```

These are intentional defaults, not guesses. The original Jarvis notes contain
a successful `gpu-l40s` job and examples for both `compute` and `gpu-l40s`.
None of those commands used `--account` or `--qos`. Before installing
anything, Step 3 asks the live Jarvis system whether your username can use the
same settings. This check does not start a real job or use a GPU.

## One-time setup

### 1. Log in to Jarvis

On your laptop, connect to the Stevens VPN. Then open Terminal and run:

```bash
ssh YOUR_STEVENS_USERNAME@jarvis.stevens.edu
```

Replace `YOUR_STEVENS_USERNAME` with your own username. Enter your Stevens
password if SSH asks for it. A Jarvis prompt usually contains a login-node name
such as `l001` or `l002`.

Important: a new student does not have a `jarvis` command. Do not type
`jarvis` by itself. Always use the full
`ssh YOUR_STEVENS_USERNAME@jarvis.stevens.edu` command. This setup does not
depend on another person's laptop, username, SSH alias, or SSH key.

Confirm where you are:

```bash
hostname
whoami
```

Do not start Qwen or vLLM yourself here. The supplied script gets a GPU first
and then starts everything in the correct place.

### 2. Download the Jarvis launcher

Run these commands on the Jarvis login node:

```bash
git clone --depth 1 https://github.com/neselab/cedar-synthesis-engine.git
cd cedar-synthesis-engine/autocedar-jarvis
cp config/jarvis.env.example config/jarvis.env
```

If the repository already exists, update it instead:

```bash
cd ~/cedar-synthesis-engine
git pull --ff-only
cd autocedar-jarvis
```

The copied configuration is already filled in for the known Jarvis L40S/Qwen
setup. Do not put a password or token in `config/jarvis.env`.

### 3. Check your Jarvis access

Run this on Jarvis:

```bash
./scripts/preflight.sh config/jarvis.env
```

This command:

- checks that you are on Jarvis;
- checks that the two computer groups exist;
- checks the GPU software supplied by Jarvis;
- asks Slurm whether your CPU and GPU settings are allowed, without starting a
  job or using a GPU;
- sends no account name and no QOS name; and
- checks for at least 50 GB of model storage.

Continue only when the last line begins with:

```text
PASS:
```

If the only failure says there is not enough model storage, ask your lab
supervisor this exact question:

```text
What full Jarvis folder path may I use to store about 50 GB of Qwen model files?
```

Then open the settings file:

```bash
nano config/jarvis.env
```

```bash
AUTOCEDAR_MODEL_CACHE="/absolute/path/your-supervisor-gave-you/autocedar/models"
```

Change only the `AUTOCEDAR_MODEL_CACHE` line to the path they give you. Save
with `Ctrl-O`, press Enter, and exit with `Ctrl-X`. Run Step 3 again.

The starting setting first tries your Jarvis scratch folder. If Jarvis has not
given you one, it tries a folder in your Jarvis home directory.

If the check says your username cannot use a computer group, or says the GPU
software is missing, send all of its output to your supervisor or Stevens
Research Computing. Do not guess a different name.

### 4. Install AutoCedar

Still on the Jarvis login node:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
uv python install 3.12
uv tool install --upgrade "autocedar>=0.2,<0.3"
autocedar --version
```

The last command must print an AutoCedar version. Then make sure future
terminals can find AutoCedar:

```bash
printf '%s\n' 'export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
```

### 5. Install the remaining software and Qwen

From `cedar-synthesis-engine/autocedar-jarvis`, run these in order:

```bash
./scripts/install-verifiers.sh config/jarvis.env
./scripts/install-vllm.sh config/jarvis.env
./scripts/prepare-model.sh config/jarvis.env
```

What they do:

- The first command installs the Cedar checking programs.
- The second command installs the program that runs Qwen.
- The third command downloads Qwen and checks the download.

The first run downloads large files and may take a while. If Jarvis says the
job is waiting in a queue, wait. Nothing is wrong. Do not close the terminal
while one of these three commands is running. If a command is interrupted, it
is safe to run that command again.

Qwen3.6-27B-FP8 is public and does not require a Hugging Face account or token.

### 6. Test everything

Submit the smoke test:

```bash
./scripts/submit-smoke-test.sh config/jarvis.env
```

Slurm will print something like:

```text
Submitted batch job 12345
```

`12345` is the automatically assigned job ID. Check it with:

```bash
squeue -u "$USER"
```

When that job disappears from the queue, replace `12345` below with the real
job ID:

```bash
cat logs/autocedar-smoke-12345.out
```

The output contains two generation tests. Both must say `OK`. This proves that
AutoCedar can talk to the local Qwen setup. It does not prove that a policy is
correct; a person must still review the meaning.

## Every time you use AutoCedar

### 1. Connect

On your laptop:

```bash
ssh YOUR_STEVENS_USERNAME@jarvis.stevens.edu
```

### 2. Enter the AutoCedar folder and launch

```bash
cd ~/cedar-synthesis-engine/autocedar-jarvis
./scripts/run-interactive.sh config/jarvis.env
```

This one command gets the L40S GPU, starts Qwen, waits until Qwen is ready, and
opens AutoCedar's text screen. It stops Qwen and gives back the GPU when you
quit.

### 3. Use AutoCedar normally

Nothing after this point is Jarvis-specific. Inside AutoCedar, you can type
normal sentences instead of preparing a file first.

For a first run, type:

```text
start a policy draft
```

AutoCedar will explain the action and ask for confirmation. After it says
drafting is active, paste or type the natural-language requirements you want
in the policy. Then type:

```text
show the draft
author this
```

AutoCedar asks for confirmation before authoring. It then proposes small schema
and policy pieces for human review.

You may also use the slash-command versions:

```text
/draft
/author
```

`/draft` starts or shows the current draft. `/author` authors the current
draft. `/settings` should show provider `local`, and `/models` should list
`autocedar-local`.

If you already have a requirements file on Jarvis, you can still use:

```text
/author /full/path/to/policy_spec.md --out /full/path/to/autocedar-runs
```

See the main [Interactive Agent Usage guide](../README.md#interactive-agent-usage)
for draft editing, saving, existing files, generated artifacts, review
commands, exporting, and troubleshooting.

### 4. Review carefully

Before approving a proposed piece, compare it with the complete natural-language
requirements and the Cedar meaning. Edit or reject anything that changes,
removes, or invents a requirement. Never use `--auto-approve` for real policy
work or a research result.

### 5. Quit cleanly

Quit AutoCedar normally or press `Ctrl-C`. Back on the login node:

```bash
squeue -u "$USER"
```

If an old job still remains, cancel it:

```bash
scancel JOB_ID
```

Run `exit` to leave Jarvis. If you first land back on a login node from an
interactive compute node, run `exit` a second time to return to your laptop.

## Why this Qwen configuration is used (you may skip this section)

The normal
[`Qwen/Qwen3.6-27B`](https://huggingface.co/Qwen/Qwen3.6-27B) weights exceed
the 48 GB VRAM of one L40S before runtime memory. The official
[`Qwen/Qwen3.6-27B-FP8`](https://huggingface.co/Qwen/Qwen3.6-27B-FP8)
download is roughly 31 GB. The supplied settings use one L40S and leave room
for Qwen to work.

The Qwen settings also:

- do not load image features that AutoCedar does not use;
- tell vLLM how to read Qwen's output; and
- turn off extra internal thinking that can use up the answer length before
  AutoCedar receives the JSON it needs.

`JARVIS_GPU_MEMORY="64G"` is CPU-side host RAM requested from Slurm. It is not
GPU VRAM, so increasing it does not fix CUDA out-of-memory errors.

Do not change the model for your first run. A different model needs different
technical settings. Ask the project maintainer to update the configuration.

## Common problems

| What you see | What it means and what to do |
| --- | --- |
| SSH times out | Connect to the Stevens VPN, then retry. |
| `Permission denied` during SSH | Confirm your Stevens username and Jarvis access. |
| Preflight says a partition is unavailable | Send the full preflight output to your supervisor or Stevens Research Computing. |
| `Invalid account or account/partition combination` | Jarvis has not connected your username to the requested computer group. Send the full error to Stevens Research Computing; do not guess an account name. |
| CUDA/cuDNN module is not found | Ask Stevens Research Computing for the module replacing `cudnn9.1-cuda12.2/9.1.1.17`, edit `JARVIS_CUDA_MODULE`, and rerun preflight. |
| Installation says `ninja` is missing | Pull the latest code, then rerun `./scripts/install-vllm.sh config/jarvis.env`. The installer now includes `ninja`. |
| vLLM reports `unsupported GNU version`, `_Float32` errors, or an error compiling `flashinfer/.../renorm.cu` | Pull the latest code, rerun `./scripts/install-vllm.sh config/jarvis.env`, and submit the smoke test again. The launcher disables FlashInfer's optional sampler and uses vLLM's built-in PyTorch sampler, which does not compile that CUDA file. |
| Model cache has less than 50 GiB or download hits quota | Set `AUTOCEDAR_MODEL_CACHE` to a larger absolute scratch/project path and rerun preflight. |
| Job says `queued and waiting for resources` | Nothing is broken. Wait, or check with `squeue -u "$USER"`. |
| vLLM exits while loading | Read `logs/vllm-JOB_ID.log`. Check the first error, not only the last line. |
| GPU out of memory | Set `AUTOCEDAR_MAX_MODEL_LEN="16384"` in `config/jarvis.env` and retry. If it still fails, send the vLLM log file to your supervisor. |
| Smoke output does not contain both `OK` lines | Confirm the Qwen defaults were not changed, rerun `install-vllm.sh`, and repeat the smoke test. |
| `autocedar doctor` reports Cedar/CVC5 failure | Rerun `install-verifiers.sh` and keep its complete output. |
| AutoCedar cannot reach the model | Always launch through `run-interactive.sh`; do not run AutoCedar or vLLM separately. |

When asking for help, send:

```bash
./scripts/preflight.sh config/jarvis.env
autocedar --version
squeue -u "$USER"
```

Also attach the relevant file from `logs/`. Do not send a password, token, or
private SSH key.

## Files in this folder

```text
README.md                              this guide
.gitignore                             keeps local config and logs out of Git
config/jarvis.env.example              ready-to-copy Jarvis/Qwen configuration
config/settings.local.json.example     optional local-provider TUI settings
scripts/preflight.sh                   live, non-allocating Jarvis check
scripts/install-verifiers.sh           one-time CPU Slurm verifier setup
scripts/install-verifiers-on-node.sh   internal verifier installer
scripts/install-vllm.sh                one-time GPU Slurm vLLM setup
scripts/install-vllm-on-node.sh        internal vLLM installer
scripts/prepare-model.sh               one-time CPU model download/check
scripts/prepare-model-on-node.sh       internal model helper
scripts/run-interactive.sh             normal launch command
scripts/run-on-node.sh                 internal GPU-node launcher
scripts/model_smoke.py                 chat and JSON-schema plumbing check
scripts/submit-smoke-test.sh           batch smoke-test wrapper
scripts/_common.sh                     shared launcher functions
slurm/autocedar-smoke.sbatch           internal smoke-test batch job
```

Run only the wrapper commands shown in the numbered steps. The files marked
“internal” are called automatically.
