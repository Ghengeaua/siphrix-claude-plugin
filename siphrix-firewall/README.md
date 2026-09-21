# Siphrix — Claude Code plugin

Audits Claude Code's tool calls through the Siphrix AI Action Audit &
Risk Monitor. It installs a **PreToolUse hook** that, before Claude
Code runs a tool, asks Siphrix for a verdict and **records** it —
risky (non-ALLOW) verdicts surface as warnings in the Siphrix views.
Nothing is blocked by default; blocking is a frozen opt-in
(`SIPHRIX_MODE=enforce`).

## Licence

Two licences, on purpose, and each file says which it carries:

- `hooks/siphrix_firewall.py`, the hook that decides whether an agent's
  action is recorded, is part of Siphrix and is under the **Business
  Source License 1.1** (the repository's `LICENSE`; the header of the
  file says so). The Siphrix engine it delegates to is not distributed
  with this plugin.
- Everything else in this folder - the manifest under `.claude-plugin/`,
  `hooks/hooks.json`, this README and the icon - is **MIT** (the
  `LICENSE` file beside this README), because the public install
  repository is MIT and a manifest that says otherwise would contradict
  the repository it sits in.

This folder is the **only place the plugin is edited**. The public
install repository, `Ghengeaua/siphrix-claude-plugin`, is a generated
copy of it, written by `tools/publish_claude_plugin.py` at release
time — two hand-maintained copies of a hook that decides whether an
agent's action is recorded had already drifted once, in version and
licence, before that script existed.

## Posture (read this first)

- **Audit-first overlay.** In the default mode (`SIPHRIX_MODE=audit`)
  every governed call is evaluated and recorded, risky verdicts feed
  the Warnings views, and the call always proceeds — an observer must
  not break the thing it observes. The hook never *grants* a tool call
  Claude Code would otherwise have gated: on ALLOW it stays silent and
  Claude Code's normal permission flow proceeds.
- **Blocking is a frozen opt-in.** Only under `SIPHRIX_MODE=enforce`
  does a non-ALLOW verdict deny the call, and only there does an
  unreachable engine (`pip install siphrix` missing) or an evaluation
  error fail closed. In the default audit mode such internal failures
  resolve to silence — the call proceeds.
- **Decision-only.** The hook asks for a verdict; it never executes the
  tool. No raw command body, file content, or path is sent to Siphrix —
  only the structured action class.

## What it governs

| Claude Code tool | Siphrix action |
| --- | --- |
| `Bash` | `shell_exec` |
| `Write` / `Edit` / `MultiEdit` / `NotebookEdit` | `file_write` |
| `Read` / `Glob` / `Grep` | `file_read` |
| `WebFetch` / `WebSearch` | `network_access` |

The actions use the shipped-pack vocabulary, so an exported pack (e.g.
`dev_agent_defaults`) governs Claude Code with no custom rules. The
mapping is shared with `siphrix agent-setup` and the settings-snippet
path — one brain, one vocabulary.

Editor-internal / bookkeeping tools (`LS`, `TodoWrite`, `Task`,
`ExitPlanMode`, …) are passed through untouched.

> **Easiest install:** run `siphrix agent-setup` — it exports the
> active policy and registers the same hook brain in your Claude Code
> `settings.json` in one idempotent step. The marketplace-plugin path
> below is equivalent for users who prefer Claude Code's plugin
> manager.

## Install

The plugin is published through the **`siphrix` marketplace**. You add
the marketplace, then install the `siphrix-firewall` plugin from it
(the id is historical and kept so existing installs keep working).

1. **Install the engine** the hook calls into:

   ```bash
   pip install siphrix
   ```

2. **Add the marketplace, then install the plugin**, inside Claude Code.

   - **From the public install repository** (no GitHub token needed):

     ```text
     /plugin marketplace add Ghengeaua/siphrix-claude-plugin
     /plugin install siphrix-firewall@siphrix
     ```

   - **From a local clone of this repository** — use the path to the
     repo root, the folder that contains `.claude-plugin/marketplace.json`,
     which points at `./tools/claude_code_plugin`:

     ```text
     /plugin marketplace add <path-to-repo-root>
     /plugin install siphrix-firewall@siphrix
     ```

   Plugins are enabled on install. Toggle with
   `/plugin disable siphrix-firewall@siphrix` /
   `/plugin enable siphrix-firewall@siphrix`. Restart Claude Code (or
   start a new session) so the PreToolUse hook loads.

   > Alternative without the marketplace: copy `hooks/hooks.json` +
   > `hooks/siphrix_firewall.py` into your project's `.claude/` and
   > reference the hook there directly.

3. (Recommended) Configure the policy the hook evaluates against by
   pointing `SIPHRIX_POLICY_FILE` at an engine policy YAML — e.g.
   export the shipped `safe_defaults` pack:

   ```bash
   siphrix pack-export --name safe_defaults --output ./policy.yaml
   export SIPHRIX_POLICY_FILE="$PWD/policy.yaml"
   ```

   Without a policy, Siphrix is empty-allowlist: every governed tool
   draws a fail-closed BLOCK verdict — recorded as a warning under the
   default audit mode (nothing is stopped), and acted on only under
   `SIPHRIX_MODE=enforce`.

## How it decides

The hook reads the PreToolUse event on stdin, maps the tool to a
`claude_code` AI-tool-bridge request, and evaluates it via the
canonical in-package adapter
(`siphrix.integrations.claude_code_hook.decide`) — the verdict is
recorded and risky verdicts surface as warnings. Only under the frozen
opt-in `SIPHRIX_MODE=enforce`, when the verdict is not ALLOW, does it
emit:

```json
{"hookSpecificOutput": {"hookEventName": "PreToolUse",
 "permissionDecision": "deny", "permissionDecisionReason": "Siphrix BLOCK: ..."}}
```

Otherwise it prints nothing and exits 0 — the call proceeds through
Claude Code's normal permission flow.

## Publishing

Never edit the public repository by hand. From this repository run

```bash
python tools/publish_claude_plugin.py --target ../../siphrix-claude-plugin
```

which copies this folder over `siphrix-firewall/` there, regenerates
the public `marketplace.json` from this repo's, and prints what
changed; then commit and push in that repository. The step sits in
`docs/release/RELEASE_RUNBOOK.md` with the other channels.
