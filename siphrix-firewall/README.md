# Siphrix — AI Action Monitor — Claude Code plugin

Records and risk-flags Claude Code's tool calls through the Siphrix AI
action monitor. It installs a **PreToolUse hook** that, before Claude
Code runs a tool, asks Siphrix for a verdict and **records** it — the
action and its risk level land in the Siphrix audit trail and
dashboards (Activity for everything, Warnings for risky actions).
Audit-first: nothing is blocked by default; `SIPHRIX_MODE=enforce`
enables the frozen legacy firewall behaviour (a non-ALLOW verdict
denies the call).

> Installable as a Claude Code plugin via the **`siphrix` marketplace**
> declared at the repo root (`.claude-plugin/marketplace.json`). See
> **Install** below. The plugin id stays `siphrix-firewall`, so
> existing installs keep working.

## Posture (read this first)

- **Audit-first.** Every governed call is evaluated and recorded; a
  BLOCK verdict is a warning ("what would have been blocked"), not an
  intervention. An observer must not break the thing it observes: in
  the default audit mode, internal failures (Siphrix missing,
  evaluation error, malformed event) resolve to silence, never to a
  deny.
- **Never grants.** On ALLOW the hook stays silent and Claude Code's
  normal permission flow proceeds — it never auto-approves a tool call
  Claude Code would otherwise have gated.
- **Frozen enforcement opt-in.** With `SIPHRIX_MODE=enforce` the legacy
  firewall behaviour returns: a non-ALLOW verdict denies the tool
  call, and failures deny fail-closed (an enforcing firewall that
  cannot reach its engine must not wave actions through).
- **Decision-only.** The hook asks for a verdict; it never executes the
  tool. No raw command body, file content, or path is sent to Siphrix —
  only the structured action class.

## What it governs

| Claude Code tool | Siphrix action |
| --- | --- |
| `Bash` | `shell_command` |
| `Write` / `Edit` / `MultiEdit` / `NotebookEdit` | `file_write` |
| `Read` | `file_read` |
| `WebFetch` / `WebSearch` | `http_request` |

Editor-internal / read-meta tools (`Glob`, `Grep`, `LS`, `TodoWrite`,
`Task`, …) are passed through untouched.

## Install

The plugin is published through the **`siphrix` marketplace**, whose
manifest lives at the **repo root** in `.claude-plugin/marketplace.json`
and points at this folder (`./siphrix-firewall`). You add the
marketplace, then install the `siphrix-firewall` plugin from it.

1. **Install the engine** the hook calls into:

   ```bash
   pip install siphrix
   ```

2. **Add the marketplace, then install the plugin**, inside Claude Code:

   ```text
   /plugin marketplace add Ghengeaua/siphrix-claude-plugin
   /plugin install siphrix-firewall@siphrix
   ```

   This repository is public, so no GitHub token is required.

   Plugins are enabled on install. Toggle with
   `/plugin disable siphrix-firewall@siphrix` /
   `/plugin enable siphrix-firewall@siphrix`. Restart Claude Code (or
   start a new session) so the PreToolUse hook loads.

   > Alternative without the marketplace: copy `hooks/hooks.json` +
   > `hooks/siphrix_firewall.py` into your project's `.claude/` and
   > reference the hook there directly.

3. (Recommended) Configure the policy Siphrix evaluates against by
   pointing `SIPHRIX_POLICY_FILE` at an engine policy YAML — e.g.
   export the shipped `safe_defaults` pack:

   ```bash
   siphrix pack-export --name safe_defaults --output ./policy.yaml
   export SIPHRIX_POLICY_FILE="$PWD/policy.yaml"
   ```

   Without a policy, Siphrix is empty-allowlist: every governed call
   records a fail-closed BLOCK verdict (`policy_empty_allowlist`),
   which shows up as a warning. In the default audit mode nothing is
   stopped; under `SIPHRIX_MODE=enforce` the hook would block every
   governed tool.

## How it decides

The hook reads the PreToolUse event on stdin and delegates to the
canonical in-package adapter
(`siphrix.integrations.claude_code_hook.decide`) — the same brain the
`siphrix agent-setup` path and the console / VS Code rule overlay
share — so tool mapping, the shared local rule overlay, policy
evaluation, and `SIPHRIX_MODE` resolution are all decided in one place,
and the verdict and risk level reach the audit trail. In the default
audit mode the call then always proceeds — the hook prints nothing and
exits 0. Only in the frozen `SIPHRIX_MODE=enforce` mode does the
adapter return a block, which the hook translates into:

```json
{"hookSpecificOutput": {"hookEventName": "PreToolUse",
 "permissionDecision": "deny", "permissionDecisionReason": "Siphrix BLOCK: ..."}}
```

Otherwise it prints nothing and exits 0.
