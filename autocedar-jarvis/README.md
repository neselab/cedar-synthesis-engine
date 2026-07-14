# AutoCedar on Stevens Jarvis with a local model

This guide is for a student who has never used Slurm before. Follow it from top
to bottom the first time. After that, use the shorter **Every time you run
AutoCedar** section.

## What you are doing

You will run two programs on one Jarvis GPU node:

1. **vLLM** loads a local language model onto the GPU and provides a private
   OpenAI-compatible HTTP server.
2. **AutoCedar** sends its model requests to that local server and checks the
   resulting Cedar policies with Cedar and CVC5.

```text
your laptop -> Stevens VPN -> Jarvis login node -> Slurm GPU node
                                                   |-- vLLM + local model
                                                   `-- AutoCedar + Cedar/CVC5
```

`AUTOCEDAR_PROVIDER=local` means “use the model server running on this machine.”
vLLM happens to expose an OpenAI-compatible HTTP protocol, but this workflow
does **not** use the OpenAI cloud API. The server in this guide listens only on
`127.0.0.1` on your assigned GPU node.

Java is not required for this AutoCedar setup.

## Before you start

You need:

- a Stevens account with Jarvis access;
- the Stevens VPN client on your laptop;
- permission to use a Jarvis GPU partition; and
- enough space in your Jarvis home or scratch directory for model weights.

The earlier Jarvis setup was verified on June 9, 2026 with the `gpu-l40s`,
`gpu-h100`, and `gpu-h100sxm` partitions and the
`cudnn9.1-cuda12.2/9.1.1.17` module. The AutoCedar code and local-provider tests
were checked locally on July 14, 2026. The combined workflow has **not** yet
been run live on Jarvis because Stevens VPN access was unavailable. If a module
or partition name has changed, ask the lab or Jarvis support before substituting
something different.

## One-time setup

### 1. Connect to Jarvis

Connect to the Stevens VPN first. Then use your own Stevens username:

```bash
ssh YOUR_STEVENS_USERNAME@jarvis.stevens.edu
```

If your laptop already has the `jarvis` SSH alias, this shorter command is
equivalent:

```bash
jarvis
```

You should first land on a login node such as `l001` or `l002`. Check:

```bash
hostname
whoami
```

Do not run a model on the login node.

### 2. Install `uv` and Python 3.12 in your account

These commands do not need administrator access:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
uv python install 3.12
```

Add this line to `~/.bashrc` so new Jarvis shells can find the tools:

```bash
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
```

You can edit that file with `nano ~/.bashrc`. Save with `Ctrl-O`, press Enter,
and exit with `Ctrl-X`.

### 3. Install the released AutoCedar package

Install the Jarvis/local-model release directly from PyPI. You do not need to
clone the repository:

```bash
uv tool install autocedar==0.1.28
autocedar --version
```

The version command must print `autocedar 0.1.28`. Clone the GitHub repository
only if your lab mentor specifically asks you to modify AutoCedar itself.

### 4. Install Cedar CLI

Cedar CLI must be built with its symbolic-analysis feature. Use a Slurm CPU
shell so the compilation does not run on the login node:

```bash
srun --mem=16G -c 4 -p compute --pty bash -i
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source "$HOME/.cargo/env"
cargo install cedar-policy-cli --locked --version 4.10.0 --features analyze --force
cedar --version
cedar symcc --help | grep principal-type
exit
```

The `grep` command should print a line containing `principal-type`. `exit`
releases the CPU job and returns you to the login node.

### 5. Install CVC5 without `sudo`

This installs the official Linux x86-64 static CVC5 binary in your account:

```bash
mkdir -p "$HOME/.local/bin" "$HOME/.local/opt"
curl -fL \
  -o "$HOME/.local/opt/cvc5-1.3.4.zip" \
  https://github.com/cvc5/cvc5/releases/download/cvc5-1.3.4/cvc5-Linux-x86_64-static.zip
unzip -q -o "$HOME/.local/opt/cvc5-1.3.4.zip" -d "$HOME/.local/opt"
ln -sfn \
  "$HOME/.local/opt/cvc5-Linux-x86_64-static/bin/cvc5" \
  "$HOME/.local/bin/cvc5"
export CVC5="$HOME/.local/bin/cvc5"
cvc5 --version
```

Also add this line to `~/.bashrc`:

```bash
export CVC5="$HOME/.local/bin/cvc5"
```

### 6. Install vLLM in a separate environment

Keep vLLM separate from AutoCedar. This prevents PyTorch/CUDA packages from
changing AutoCedar's smaller Python environment.

First request one L40S GPU:

```bash
srun --mem=64G -c 2 --gres=gpu:1 -p gpu-l40s --pty bash -i
```

Your hostname should now look like a GPU node rather than `l001` or `l002`.
Then run:

```bash
module load cudnn9.1-cuda12.2/9.1.1.17
nvidia-smi
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
uv venv "$HOME/.venvs/autocedar-vllm" --python 3.12
source "$HOME/.venvs/autocedar-vllm/bin/activate"
uv pip install vllm --torch-backend=auto
vllm --version
deactivate
exit
```

`exit` releases this one-time interactive GPU job and returns you to the login
node.

## Every time you run AutoCedar

### 1. Connect and request a GPU

From your laptop:

```bash
ssh YOUR_STEVENS_USERNAME@jarvis.stevens.edu
```

On the Jarvis login node:

```bash
srun --mem=64G -c 2 --gres=gpu:1 -p gpu-l40s --pty bash -i
```

On the assigned GPU node:

```bash
module load cudnn9.1-cuda12.2/9.1.1.17
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
export CVC5="$HOME/.local/bin/cvc5"
hostname
nvidia-smi
```

### 2. Start the local model server

The starter model below is small enough to test the plumbing on one L40S. It
is a feasibility model, not a claim that it matches the quality of Codex or a
larger lab-approved model.

```bash
export MODEL_REPO="Qwen/Qwen2.5-Coder-7B-Instruct"
export MODEL_NAME="autocedar-local"
export MODEL_KEY="autocedar-local"
export MODEL_PORT="8000"
export HF_HOME="${SCRATCH:-$HOME/.cache}/huggingface"
export VLLM_LOG="$HOME/vllm-${SLURM_JOB_ID}.log"
mkdir -p "$HF_HOME"

"$HOME/.venvs/autocedar-vllm/bin/vllm" serve "$MODEL_REPO" \
  --host 127.0.0.1 \
  --port "$MODEL_PORT" \
  --served-model-name "$MODEL_NAME" \
  --api-key "$MODEL_KEY" \
  --max-model-len 32768 \
  --gpu-memory-utilization 0.90 \
  >"$VLLM_LOG" 2>&1 &
export VLLM_PID=$!
echo "vLLM process: $VLLM_PID"
echo "vLLM log: $VLLM_LOG"
```

The first run downloads the model and may take several minutes. Wait until the
server answers:

```bash
until curl -fsS \
  -H "Authorization: Bearer $MODEL_KEY" \
  "http://127.0.0.1:${MODEL_PORT}/v1/models"
do
  if ! kill -0 "$VLLM_PID" 2>/dev/null; then
    echo "vLLM stopped. Read the log below."
    tail -n 80 "$VLLM_LOG"
    break
  fi
  echo "Still loading; waiting 5 seconds..."
  sleep 5
done
```

If this waits for more than ten minutes, press `Ctrl-C` and read the last part
of the log:

```bash
tail -n 80 "$VLLM_LOG"
```

### 3. Point AutoCedar at vLLM

Run these commands in the **same GPU-node shell**:

```bash
export AUTOCEDAR_PROVIDER="local"
export AUTOCEDAR_LOCAL_BASE_URL="http://127.0.0.1:${MODEL_PORT}/v1"
export AUTOCEDAR_LOCAL_API_KEY="$MODEL_KEY"
export AUTOCEDAR_LOCAL_MODEL="$MODEL_NAME"
export AUTOCEDAR_MODEL="$MODEL_NAME"
export AUTOCEDAR_LOCAL_MAX_TOKENS="8192"
export AUTOCEDAR_LOCAL_TIMEOUT_SECONDS="600"

autocedar doctor
```

The important `doctor` lines should say:

- the local model server is reachable;
- `autocedar-local` is advertised;
- Cedar CLI 4.10.0 is available with the SymCC interface;
- CVC5 is available; and
- the live SymCC smoke test passes.

Fix every `FAIL` before starting real authoring.

### 4. Run AutoCedar

The easiest interface is the terminal UI:

```bash
autocedar
```

Inside AutoCedar, check the connection:

```text
/settings
/models
```

Then start a lab-provided specification:

```text
/author /full/path/to/policy_spec.md --out /full/path/to/autocedar-runs --model autocedar-local
```

You can also run the same workflow directly from the shell:

```bash
autocedar author /full/path/to/policy_spec.md \
  --out "$HOME/autocedar-runs" \
  --model "$MODEL_NAME"
```

Use full paths until you are comfortable with Linux directories.

## The human review is the important part

AutoCedar will pause and show one proposed schema or policy property at a time.
Your job is to compare all three things:

1. the original natural-language requirement;
2. the proposed atom; and
3. the Cedar declaration or policy meaning.

The review keys are:

| Key | Meaning | When to use it |
| --- | --- | --- |
| `A` | Approve | The atom says exactly what the requirement intends. |
| `R` | Reject | It is wrong or adds/removes a requirement. Give a reason. |
| `E` | Edit | A specific field can be corrected directly. |
| `Q` | Question | You do not understand the proposal yet. |
| `S` | See Cedar | Inspect the generated Cedar before deciding. |
| `V` | View patches | Inspect a proposed change when patches are available. |

Do not approve an atom merely because it looks technical or because AutoCedar
reports that it is symbolically consistent. Symbolic consistency does not prove
that the atom matches the human requirement.

Do **not** use `--auto-approve` for a real policy or research evaluation. That
option is only for automated plumbing tests and is not human-in-the-loop
validation.

## Stop cleanly

Exit AutoCedar, then stop vLLM and leave the GPU node:

```bash
kill "$VLLM_PID"
wait "$VLLM_PID" 2>/dev/null || true
exit
```

On the login node, confirm that no job is still running:

```bash
squeue -u "$USER"
```

If a forgotten job remains, stop it with:

```bash
scancel JOB_ID
```

## Common problems

| Problem | What to do |
| --- | --- |
| SSH cannot reach Jarvis | Connect to Stevens VPN and retry. |
| Local server is unreachable | Confirm vLLM and AutoCedar are in the same GPU-node shell. Run `ps -p "$VLLM_PID"` and `tail -n 80 "$VLLM_LOG"`. |
| Model is not advertised | Make `--served-model-name` and `AUTOCEDAR_LOCAL_MODEL` identical. |
| GPU out of memory | Change `--max-model-len 32768` to `16384`, set `AUTOCEDAR_LOCAL_MAX_TOKENS=4096`, and restart vLLM; or use an approved H100 partition. |
| Cedar or CVC5 fails | Run both binaries by full path, export the paths, then rerun `doctor`. |

Useful verifier check:

```bash
"$HOME/.cargo/bin/cedar" --version
"$HOME/.local/bin/cvc5" --version
export CEDAR="$HOME/.cargo/bin/cedar"
export CVC5="$HOME/.local/bin/cvc5"
autocedar doctor
```

For a CUDA/PyTorch import error, do not reuse an older general-purpose virtual
environment. Move the vLLM environment aside and recreate it inside a GPU job:

```bash
mv "$HOME/.venvs/autocedar-vllm" \
  "$HOME/.venvs/autocedar-vllm-old-$(date +%Y%m%d-%H%M%S)"
uv venv "$HOME/.venvs/autocedar-vllm" --python 3.12
source "$HOME/.venvs/autocedar-vllm/bin/activate"
uv pip install vllm --torch-backend=auto
```

For a structured-output error, update vLLM first. As a less reliable last
resort, set `AUTOCEDAR_LOCAL_STRUCTURED_OUTPUT=prompt` and record that change
in the experiment notes.

Do not silently change the model in a research run. Record the model repository,
served name, vLLM version, GPU type, and context length.

## Official references

- [vLLM GPU installation](https://docs.vllm.ai/en/latest/getting_started/installation/gpu/)
- [vLLM quickstart](https://docs.vllm.ai/en/latest/getting_started/quickstart/)
- [vLLM structured outputs](https://docs.vllm.ai/en/latest/features/structured_outputs/)
- [CVC5 downloads](https://cvc5.github.io/downloads.html)
- [Cedar CLI 4.10.0 features](https://docs.rs/crate/cedar-policy-cli/4.10.0/features)
