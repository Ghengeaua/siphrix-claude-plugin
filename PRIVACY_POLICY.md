# Privacy Policy — Siphrix browser extension

_Last updated: 2026-06-09_

The Siphrix browser extension ("the extension") is designed to protect
your data, not collect it.

## What the extension does

The extension watches file uploads and clipboard pastes on a fixed set of
AI web apps (ChatGPT, Claude, Gemini, Copilot, Perplexity) and asks your
**local** Siphrix engine whether the action is allowed by your policy.

## Data we collect and where it goes

- **We do not collect, sell, or transmit your personal data to any remote
  server.** The extension communicates **only** with the Siphrix software
  running on your own computer (loopback addresses `127.0.0.1`).
- **File contents and pasted text never leave the page.** Secret-shape
  detection happens locally inside the extension. Only a small amount of
  **structured metadata** — the site's domain and an action type such as
  `upload_file` — is sent to your **local** Siphrix service to obtain a
  policy verdict.
- **Local storage.** The extension stores your settings and, if you log
  in to your Siphrix account, a **session token**, in the browser's
  extension storage on your device. This information stays on your device
  and is used only to authenticate to your local Siphrix service.

## What we do NOT do

- We do not use analytics or tracking.
- We do not share or sell any data to third parties.
- We do not use your data for advertising, creditworthiness, or any
  purpose unrelated to the extension's single purpose (gating AI actions
  through your local Siphrix policy).

## Permissions

- `storage` — to keep your settings and session token on your device.
- Host access to `127.0.0.1` — to talk to your local Siphrix engine and
  account service; no remote hosts are contacted.
- Content scripts on the listed AI sites — to detect uploads and
  secret-shaped pastes so they can be gated.

## Contact

For privacy questions, contact the developer at the email listed on the
Chrome Web Store listing.
