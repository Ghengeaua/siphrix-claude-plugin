#!/usr/bin/env python3
# Licence: Business Source License 1.1 - this file is part of Siphrix and
# carries the repository's licence, not the MIT licence of the plugin
# scaffolding around it (see ../LICENSE). It is the file that decides
# whether an agent's action is recorded; that is the product, and the
# product is BUSL. The manifest, hooks.json, README and icon are MIT so
# that the public install repository, which is MIT, is not contradicted
# by the manifest it ships. Decided 2026-09-21.
"""Siphrix PreToolUse hook for Claude Code — audit & risk monitor.

Claude Code invokes this script before it runs a tool. The script
delegates mapping and evaluation to the canonical in-package adapter
(:mod:`siphrix.integrations.claude_code_hook`) — one brain, shared with
the console / VS Code rule overlay and the ``siphrix agent-setup``
settings-snippet path — and answers in the plugin hook protocol: to
deny (frozen enforce mode only), it prints a ``hookSpecificOutput``
object with ``permissionDecision: "deny"``; otherwise it prints nothing
and exits 0.

Posture:

* **Audit-first.** In the default mode (``SIPHRIX_MODE=audit``) every
  governed call is evaluated and recorded — the Activity and Warnings
  dashboards show what happened and what looked risky — and always
  proceeds. An observer must not break the thing it observes: engine
  failures resolve to silence, never to a deny.
* **Fail-closed only in the frozen enforce mode**
  (``SIPHRIX_MODE=enforce``): a non-ALLOW verdict, or any failure to
  reach the engine, denies the governed call with a clear reason.
* **Decision-only, fully local.** The hook asks the local engine for a
  verdict in-process; nothing leaves the machine, it never executes the
  tool itself, and raw params (commands, paths) are redacted by the
  audit writer before any record is written.
* **Never grants.** On ALLOW (or for editor-internal meta tools) the
  hook stays silent and lets Claude Code's normal permission flow
  proceed — it does not auto-approve and so never weakens Claude
  Code's own guardrails.
* **One brain.** By delegating to the canonical adapter, the local rule
  overlay (console / VS Code rules), the policy engine, and the
  ``SIPHRIX_MODE`` resolution are all shared with every other Siphrix
  integration — the plugin never re-implements the decision itself.

Hook protocol: reads the PreToolUse event JSON on stdin and, to deny
(enforce mode only), prints a ``hookSpecificOutput`` object with
``permissionDecision: "deny"``. Otherwise it prints nothing and
exits 0.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, Optional

# Local mirror of the canonical governed-tool scope. Kept here so the
# "meta tools pass through" guarantee holds even when the siphrix
# package is missing (in which case governed tools are silent in audit
# mode / denied fail-closed under enforce, but TodoWrite / Task /
# ExitPlanMode still work).
_GOVERNED_TOOLS = frozenset(
    {
        "Bash",
        "Write",
        "Edit",
        "MultiEdit",
        "NotebookEdit",
        "Read",
        "Glob",
        "Grep",
        "WebFetch",
        "WebSearch",
    }
)


def _deny(reason: str) -> Dict[str, Any]:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def _enforcement_enabled() -> bool:
    """Enforcement is a frozen, explicit opt-in; audit is the default.

    Prefers the canonical switch in :mod:`siphrix.mode`; falls back to
    reading the env var directly so the audit-mode "never break the
    workflow" guarantee holds even when the siphrix package is absent.
    """
    try:
        from siphrix.mode import enforcement_enabled

        return enforcement_enabled()
    except Exception:
        return os.environ.get("SIPHRIX_MODE", "").strip().lower() == "enforce"


def decide(event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Decide on one PreToolUse event.

    Returns a deny payload dict to block (frozen enforce mode only),
    or ``None`` to stay silent and let Claude Code's normal flow
    proceed. In audit mode the canonical adapter still evaluates and
    records the decision (consulting the shared local overlay), and
    every failure resolves to silence — the default mode NEVER denies.
    """
    tool_name = event.get("tool_name")
    if not isinstance(tool_name, str) or tool_name not in _GOVERNED_TOOLS:
        # Not a governed tool — let Claude Code's own flow handle it.
        return None

    enforce = _enforcement_enabled()

    try:
        from siphrix.integrations.claude_code_hook import (
            EXIT_BLOCK,
            decide as canonical_decide,
        )
    except Exception:
        if enforce:
            # The firewall cannot reach its engine: fail closed.
            return _deny(
                "Siphrix firewall unavailable (pip install siphrix). "
                "Fail-closed: tool call blocked."
            )
        # Audit mode: nothing to record with, nothing to break.
        return None

    try:
        code, message = canonical_decide(event)
    except Exception:
        if enforce:
            return _deny("Siphrix evaluation error. Fail-closed: tool call blocked.")
        return None

    if code == EXIT_BLOCK:
        # The canonical adapter only returns EXIT_BLOCK in enforce mode
        # (it resolves SIPHRIX_HOOK_MODE / SIPHRIX_MODE itself, sharing
        # the overlay + engine), so this path is already the frozen
        # opt-in. In the default audit mode it never returns EXIT_BLOCK,
        # so this hook never denies.
        return _deny(message or "Siphrix blocked this action.")
    # Never auto-approve; defer to Claude Code's normal permission flow.
    return None


def main() -> int:
    try:
        raw = sys.stdin.read()
        event = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, UnicodeDecodeError):
        # A malformed event is suspicious; deny only when enforcing.
        if _enforcement_enabled():
            print(json.dumps(_deny("Siphrix: unreadable PreToolUse event. Fail-closed.")))
        return 0
    if not isinstance(event, dict):
        if _enforcement_enabled():
            print(json.dumps(_deny("Siphrix: invalid PreToolUse event. Fail-closed.")))
        return 0
    decision = decide(event)
    if decision is not None:
        print(json.dumps(decision))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
