<p align="center">
  <img src="siphrix-firewall/icon.png" alt="Siphrix" width="120">
</p>

# Siphrix firewall — Claude Code plugin

Gate every Claude Code tool call through the **[Siphrix](https://pypi.org/project/siphrix/) AI action firewall**.
Before Claude Code runs a tool (`Bash`, `Write`, `Edit`, `WebFetch`, …),
the plugin asks Siphrix for a verdict and **blocks** the call on a
non-ALLOW verdict.

This repository is the **public install source** for the plugin. The
Siphrix engine itself ships on PyPI (`pip install siphrix`); this repo
contains only the Claude Code integration.

## Posture

- **Block-only.** Siphrix can *add* a block; it never *grants* a call
  Claude Code would otherwise gate.
- **Fail-closed.** If the engine is not importable or evaluation errors,
  the tool call is **denied** — a firewall that can't reach its engine
  must not wave actions through.
- **Decision-only.** The hook asks for a verdict; it never executes the
  tool. Only the structured action class is sent to Siphrix — no raw
  command body, file content, or path.

## Install

1. Install the engine the hook calls into:

   ```bash
   pip install siphrix
   ```

2. In Claude Code, add this marketplace and install the plugin:

   ```text
   /plugin marketplace add Ghengeaua/siphrix-claude-plugin
   /plugin install siphrix-firewall@siphrix
   ```

   Then restart Claude Code (or start a new session) so the PreToolUse
   hook loads. Toggle with `/plugin disable siphrix-firewall@siphrix` /
   `/plugin enable siphrix-firewall@siphrix`.

3. (Recommended) Point the firewall at a policy — otherwise Siphrix is
   default-deny (fail-closed) and blocks every governed tool:

   ```bash
   siphrix pack-export --name safe_defaults --output ./policy.yaml
   export SIPHRIX_POLICY_FILE="$PWD/policy.yaml"   # PowerShell: $env:SIPHRIX_POLICY_FILE="$PWD\policy.yaml"
   ```

## What it governs

| Claude Code tool | Siphrix action |
| --- | --- |
| `Bash` | `shell_command` |
| `Write` / `Edit` / `MultiEdit` / `NotebookEdit` | `file_write` |
| `Read` | `file_read` |
| `WebFetch` / `WebSearch` | `http_request` |

Editor-internal / read-meta tools (`Glob`, `Grep`, `LS`, `TodoWrite`,
`Task`, …) are passed through untouched.

See [`siphrix-firewall/README.md`](siphrix-firewall/README.md) for the
full hook details.

## License

MIT
