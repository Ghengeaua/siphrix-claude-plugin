#!/usr/bin/env python3
"""Siphrix PreToolUse hook for Claude Code — a block-only firewall overlay.

Claude Code invokes this script before it runs a tool. The script maps
the proposed tool call to a Siphrix action, evaluates it through the
public Siphrix policy engine (the ``claude_code`` AI-tool-bridge
profile), and **blocks** the tool call when Siphrix returns a non-ALLOW
verdict. It never *grants* a tool call that Claude Code would otherwise
have gated — exactly the block-only-overlay posture the local daemon
uses ("Siphrix can add blocks; it never unblocks").

Posture:

* **Fail-closed.** If Siphrix cannot be imported or evaluation raises,
  the hook DENIES the tool call with a clear reason. A security overlay
  that cannot reach its engine must not wave actions through. Install
  Siphrix (``pip install siphrix``) for the plugin to function.
* **Decision-only.** The hook asks Siphrix for a verdict; it never
  executes the tool itself.
* **Block-only.** On ALLOW (or for editor-internal meta tools) the hook
  stays silent and lets Claude Code's normal permission flow proceed —
  it does not auto-approve and so never weakens Claude Code's own
  guardrails.

Hook protocol: reads the PreToolUse event JSON on stdin and, to block,
prints a ``hookSpecificOutput`` object with ``permissionDecision:
"deny"``. To allow, it prints nothing and exits 0.
"""

from __future__ import annotations

import json
import sys
from typing import Any, Dict, Optional

# Map Claude Code tool names to the Siphrix claude_code bridge profile.
# Editor-internal / read-meta tools (Glob, Grep, LS, TodoWrite, Task,
# ExitPlanMode, …) are not security-relevant side effects, so they are
# intentionally absent: the hook passes them through untouched.
_TOOL_MAP: Dict[str, Dict[str, str]] = {
    "Read": {"action_name": "file_read", "effect_type": "read_only", "risk_level": "LOW"},
    "Write": {"action_name": "file_write", "effect_type": "local_write", "risk_level": "MEDIUM"},
    "Edit": {"action_name": "file_write", "effect_type": "local_write", "risk_level": "MEDIUM"},
    "MultiEdit": {"action_name": "file_write", "effect_type": "local_write", "risk_level": "MEDIUM"},
    "NotebookEdit": {"action_name": "file_write", "effect_type": "local_write", "risk_level": "MEDIUM"},
    "Bash": {"action_name": "shell_command", "effect_type": "local_write", "risk_level": "HIGH"},
    "WebFetch": {"action_name": "http_request", "effect_type": "network_call", "risk_level": "HIGH"},
    "WebSearch": {"action_name": "http_request", "effect_type": "network_call", "risk_level": "MEDIUM"},
}


def map_tool_call(tool_name: str, tool_input: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Map a Claude Code tool call to a Siphrix bridge request payload.

    Returns ``None`` for tools that are not security-relevant side
    effects (the hook passes those through). ``tool_input`` is used only
    for a short, non-leaky command summary — never the raw body.
    """
    spec = _TOOL_MAP.get(tool_name)
    if spec is None:
        return None
    payload: Dict[str, Any] = {
        "client_id": "claude_code",
        "tool_name": spec["action_name"],
        "action_name": spec["action_name"],
        "risk_level": spec["risk_level"],
        "effect_type": spec["effect_type"],
        "metadata": {"source_tool": tool_name},
    }
    return payload


def _deny(reason: str) -> Dict[str, Any]:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def decide(event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Decide on one PreToolUse event.

    Returns a deny payload dict to block, or ``None`` to stay silent and
    let Claude Code's normal flow proceed. Fail-closed: any failure to
    reach or run the Siphrix engine returns a deny.
    """
    tool_name = event.get("tool_name")
    tool_input = event.get("tool_input")
    if not isinstance(tool_name, str):
        return None
    payload = map_tool_call(tool_name, tool_input if isinstance(tool_input, dict) else {})
    if payload is None:
        # Not a governed tool — let Claude Code's own flow handle it.
        return None

    try:
        from siphrix.console.ai_tool_bridge import evaluate_ai_tool_request
    except Exception:
        # The firewall cannot reach its engine: fail closed.
        return _deny("Siphrix firewall unavailable (pip install siphrix). Fail-closed: tool call blocked.")

    try:
        evaluation = evaluate_ai_tool_request(payload)
    except Exception:
        return _deny("Siphrix evaluation error. Fail-closed: tool call blocked.")

    if evaluation.get("allowed") is True:
        # Block-only overlay: never auto-approve; defer to Claude Code's
        # normal permission flow.
        return None
    verdict = evaluation.get("verdict", "BLOCK")
    reason = evaluation.get("reason", "blocked")
    return _deny(f"Siphrix {verdict}: {tool_name} -> {payload['action_name']} ({reason}).")


def main() -> int:
    try:
        raw = sys.stdin.read()
        event = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, UnicodeDecodeError):
        # A malformed event from the host is itself suspicious; fail closed.
        print(json.dumps(_deny("Siphrix: unreadable PreToolUse event. Fail-closed.")))
        return 0
    if not isinstance(event, dict):
        print(json.dumps(_deny("Siphrix: invalid PreToolUse event. Fail-closed.")))
        return 0
    decision = decide(event)
    if decision is not None:
        print(json.dumps(decision))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
