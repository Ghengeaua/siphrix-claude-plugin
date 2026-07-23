<p align="center">
  <img src="siphrix-firewall/icon.png" alt="Siphrix" width="120">
</p>

# Siphrix — AI Action Monitor — Claude Code plugin

Record and risk-flag every governed Claude Code tool call through the
**[Siphrix](https://pypi.org/project/siphrix/) AI action monitor**.
Before Claude Code runs a tool (`Bash`, `Write`, `Edit`, `WebFetch`, …),
the plugin asks Siphrix for a verdict and **records** it — the action
and its risk level land in the Siphrix audit trail and dashboards
(Activity for everything, Warnings for risky actions). Audit-first:
**nothing is blocked by default**. `SIPHRIX_MODE=enforce` enables the
frozen legacy firewall behaviour.

This repository is the **public install source** for the plugin (the
plugin id stays `siphrix-firewall`, so existing installs keep working).
The Siphrix engine itself ships on PyPI (`pip install siphrix`); this
repo contains only the Claude Code integration.

## Posture

- **Audit-first.** Every governed call is evaluated and recorded;
  BLOCK verdicts are warnings ("what would have been blocked"), not
  interventions. An observer must not break the thing it observes: in
  the default mode, internal failures resolve to silence, never to a
  deny.
- **Never grants.** On ALLOW the hook stays silent — it never
  auto-approves a call Claude Code would otherwise gate.
- **Frozen enforcement opt-in.** `SIPHRIX_MODE=enforce` restores the
  legacy firewall: a non-ALLOW verdict denies the call, and engine
  failures deny fail-closed.
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

3. (Recommended) Point Siphrix at a policy — without one, every
   governed call records a fail-closed BLOCK verdict
   (`policy_empty_allowlist`) that shows up as a warning. In the
   default audit mode nothing is stopped; under `SIPHRIX_MODE=enforce`
   it would block every governed tool:

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
