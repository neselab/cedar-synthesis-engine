# Model providers and configuration

AutoCedar has five first-class model providers. Provider IDs are stable and
may be used in the TUI, CLI, environment variables, and saved settings.

| Provider ID | Authentication | Default model |
| --- | --- | --- |
| `codex` | Existing Codex login (`codex login`) | `gpt-5.5` |
| `claude-cli` | Existing Claude Code login (`claude auth login`) | `sonnet` |
| `anthropic` | Anthropic API key | `claude-opus-4-7` |
| `openai` | OpenAI platform API key | `gpt-5.6` |
| `local` | Local OpenAI-compatible endpoint; key optional | `autocedar-local` |

`openai` means the direct OpenAI API. It is deliberately separate from
`codex`, which uses the user's Codex login. `claude-cli` runs the installed
`claude -p` command; it is deliberately separate from `anthropic`, which bills
an Anthropic API key.

## Configure from the TUI

Start AutoCedar and use these commands:

```text
/settings
/provider codex|claude-cli|anthropic|openai|local
/login
/logout
/models
/model MODEL
/effort low|medium|high|max
/endpoint http://127.0.0.1:8000/v1
```

- `/provider` selects and saves the default provider.
- `/login` starts the provider's normal login flow. For API-key providers it
  prompts for the key without echoing it. For Codex and Claude CLI it invokes
  their official login commands and does not copy their credential files.
- `/logout` removes AutoCedar's saved API key or invokes the provider CLI's
  logout flow. It never deletes another tool's credential files itself.
- `/models` lists discoverable models when the provider supports discovery.
- `/model` and `/effort` are saved per provider, so switching providers does
  not accidentally reuse an incompatible model name.
- `/endpoint` configures `local`; the server and AutoCedar must be reachable
  from the same machine or cluster node when using `127.0.0.1`.

`/apikey` remains as a compatibility alias for API-key setup, but `/login` is
the provider-neutral command new users should learn.

## Configure from the command line

The same settings are available without opening the TUI:

```bash
# Inspect the effective provider configuration and where each value came from.
autocedar config

# Save a provider and its provider-specific model/effort.
autocedar config --provider codex --model gpt-5.5 --effort high
autocedar config --provider local \
  --model the-served-model-name \
  --endpoint http://127.0.0.1:8000/v1

# Inspect, add, or remove authentication for the selected provider.
autocedar auth status
autocedar auth login openai
autocedar auth logout openai
```

`autocedar author`, `resume`, and `synthesize` also accept `--provider` for a
single run without changing the saved default. Use `autocedar COMMAND --help`
for the complete provider/model options on that command.

## Where configuration is stored

AutoCedar separates non-secret settings from credentials:

```text
~/.config/autocedar/settings.json   provider, model, effort, endpoint
~/.config/autocedar/auth.json       provider-scoped API keys
```

The directory is created with mode `0700`; both files are written atomically
with mode `0600`. AutoCedar never copies Codex or Claude Code OAuth/session
credentials into these files.

An older `~/.config/autocedar/.env` is imported once for compatibility and is
left untouched. The migration marker prevents a removed key from being
silently imported again.

## Configuration precedence

For a setting or key, the first available source wins:

1. a current-session CLI/TUI override;
2. an existing shell variable or the nearest project `.env` loaded at startup;
3. AutoCedar's `settings.json` or `auth.json`;
4. the provider default.

This makes project-specific configuration possible without overwriting a
user's normal defaults. `/settings` in the TUI and `autocedar config` in the
shell report the effective values and their sources.

## Environment-variable configuration

Environment variables remain useful for automation and Slurm jobs:

```dotenv
AUTOCEDAR_PROVIDER=codex
AUTOCEDAR_CODEX_MODEL=gpt-5.5
AUTOCEDAR_EFFORT=high

# Claude Code subscription through `claude -p`
# AUTOCEDAR_PROVIDER=claude-cli
# AUTOCEDAR_CLAUDE_CLI_MODEL=sonnet

# Direct Anthropic API
# AUTOCEDAR_PROVIDER=anthropic
# ANTHROPIC_API_KEY=...
# AUTOCEDAR_ANTHROPIC_MODEL=claude-opus-4-7

# Direct OpenAI API
# AUTOCEDAR_PROVIDER=openai
# OPENAI_API_KEY=...
# AUTOCEDAR_OPENAI_MODEL=gpt-5.6

# Local OpenAI-compatible endpoint
# AUTOCEDAR_PROVIDER=local
# AUTOCEDAR_LOCAL_BASE_URL=http://127.0.0.1:8000/v1
# AUTOCEDAR_LOCAL_API_KEY=optional-local-token
# AUTOCEDAR_LOCAL_MODEL=the-served-model-name
```

Do not put real keys in a repository. Project `.env` files are ignored by this
repository, but saved provider credentials are safer for normal interactive
use.

## Local servers and Jarvis

The `local` provider uses an OpenAI-compatible Chat Completions endpoint. The
model name must exactly match the name advertised by the server. A key is
optional because many loopback-only servers do not require one.

Stevens/Jarvis-specific Slurm instructions and templates live only in
[`autocedar-jarvis/`](../autocedar-jarvis/README.md). The Python package itself
contains no Stevens paths, accounts, partitions, or model-cache assumptions.

## Authentication safety

- Prompts are passed to `claude -p` on standard input, not interpolated into a
  shell command.
- The Claude CLI backend disables tools, slash commands, MCP, and session
  persistence for model calls.
- AutoCedar never accepts shell commands as credential providers.
- Status output reports whether credentials are present and where the setting
  came from, but never prints a full API key.
