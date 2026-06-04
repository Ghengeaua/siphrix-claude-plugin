# Siphrix — Claude Code plugin

Gates Claude Code's tool calls through the Siphrix AI action firewall.
It installs a **PreToolUse hook** that, before Claude Code runs a tool,
asks Siphrix for a verdict and **blocks** the call on a non-ALLOW
verdict.

> Installable as a Claude Code plugin via the **`siphrix` marketplace**
> declared at the repo root (`.claude-plugin/marketplace.json`). See
> **Install** below.

## Posture (read this first)

- **Block-only overlay.** Siphrix can *add* a block; it never *grants* a
  tool call Claude Code would otherwise have gated. On ALLOW the hook
  stays silent and Claude Code's normal permission flow proceeds.
- **Fail-closed.** If Siphrix is not importable (`pip install siphrix`)
  or evaluation errors, the hook **denies** the tool call. A firewall
  that cannot reach its engine must not wave actions through.
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

3. (Recommended) Configure the policy the firewall enforces by pointing
   `SIPHRIX_POLICY_FILE` at an engine policy YAML — e.g. export the
   shipped `safe_defaults` pack:

   ```bash
   siphrix pack-export --name safe_defaults --output ./policy.yaml
   export SIPHRIX_POLICY_FILE="$PWD/policy.yaml"
   ```

   Without a policy, Siphrix is empty-allowlist (default-deny): the hook
   will block every governed tool. That is the fail-closed default.

## How it decides

The hook reads the PreToolUse event on stdin, maps the tool to a
`claude_code` AI-tool-bridge request, evaluates it via the public
`siphrix.console.ai_tool_bridge.evaluate_ai_tool_request`, and — only
when the verdict is not ALLOW — emits:

```json
{"hookSpecificOutput": {"hookEventName": "PreToolUse",
 "permissionDecision": "deny", "permissionDecisionReason": "Siphrix BLOCK: ..."}}
```

Otherwise it prints nothing and exits 0.
