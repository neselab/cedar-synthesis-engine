# AutoCedar plugin

This plugin is for Claude Code and Codex. It turns natural-language
access-control requirements into Cedar policies that are verified against a
target you review.

It contains:

- `skills/autocedar/SKILL.md`, which tells the agent how to run AutoCedar and
  that every atom decision is yours;
- an MCP server, started as `uvx --from "autocedar>=0.3.0" autocedar mcp`, with the tools
  `doctor`, `verify`, `author_start`, `author_status`, `author_review` and
  `author_pause`.

Manifests: `.claude-plugin/plugin.json` (Claude Code) and `.codex-plugin/plugin.json`
(Codex). Claude Code reads the MCP config from `.mcp.json` and Codex from
`codex-mcp.json`.

See "Option D" in the repository README for install commands.
