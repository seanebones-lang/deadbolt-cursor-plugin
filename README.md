# DeadBolt for Cursor

**Give agents tools. Keep control.** A free Apache-2.0 local MCP plugin from
[NextEleven](https://www.nexteleven.dev/deadbolt).

This plugin includes the exact released **MCP bundle 1.1.0**, containing stable
**engine 1.0.3**. Plugin version **1.0.0** is a separate packaging version.
It needs Node.js 20+ on PATH. macOS Apple Silicon/Intel, Linux x64 with glibc,
and Windows x64 are included. It requires no Rust build, API key or hosted gate.

## Start with read-only setup

Leave `DEADBOLT_OPERATOR_CONFIG` blank. Cursor discovers:

- `deadbolt_get_integration_guide`: local setup instructions for stdio, Rust,
  HTTP or Claude Desktop.
- `deadbolt_check_bundle`: hashes this host's packaged engine and reports the
  packaging versions, compatibility and scope.

**Setup mode provides no active protection.** It starts no downstream server,
reads no accounts, creates no policy/state and makes no network requests.
`checksum_matches` checks packaged integrity, not independent certification.

For local development, copy this entire repository to
`~/.cursor/plugins/local/deadbolt` (use actual files, not an external symlink),
reload Cursor, and inspect Customize → Plugins and MCP. This loads local code
with your user's privileges; review it before enabling. Marketplace publication
requires Cursor review; repository availability does not establish acceptance.

## Gate one trusted server

1. Create a private operator-owned directory outside the agent's workspace.
2. Copy `bundle/operator-config.example.json` there. Replace every placeholder
   with absolute paths, a fresh run ID, an explicit tool allow-list, destinations,
   irreversible-tool classification and your spend cap. Never commit that file.
3. In the plugin's Configure controls, set `DEADBOLT_OPERATOR_CONFIG` to the
   absolute JSON path. Restart its MCP connection. When configuration is valid,
   setup tools are replaced by the trusted downstream server's tools. Invalid
   supplied configuration refuses startup; it does not fall back to setup.
4. Verify an allowed dummy effect and a denied dummy effect before using accounts.
   Follow the [editor evaluation](https://seanebones-lang.github.io/deadbolt/editor-tutorial.html).
5. Keep policy, approval, pause, clip, resume and kill in the operator's local CLI,
   outside model tools. The signed native CLI is included in `bundle/native/`.

If Configure is unavailable for your account, use the existing
[editor helper](https://seanebones-lang.github.io/deadbolt/editors.html) to install
and configure the verified release as a normal local MCP connection. Do not
modify plugin source to store a private path or a credential. Do not run both
connections against the same run identity.

The stable engine has a 60-second sliding lease. Silence expires it. Use a fresh
operator-assigned identity for a new run, and never reuse a killed identity or
share one across concurrent sessions. Stable classified irreversible tools use
a broad one-shot grant; the **engine 1.1.0-rc.1** exact-action features are not in
this plugin. Choose that engine separately when those features are required.

## The execution boundary

Only routed `tools/call` requests are gated. Downstream startup, other MCP
methods, arbitrary OS/network access and already-running tool bodies are outside
that boundary. The downstream process stays trusted and runs with your user's
privileges. It can access the environment normally available to that process;
connect only reviewed servers. Client consent and DeadBolt approval are separate.
Unprotected Cursor tools and other installed MCP servers are not covered.

This is a permission gate, not an OS sandbox or a compliance certification.
Open policy is the engine default; this launcher's configured mode requires an
explicit nonempty tool allow-list. Reported spend depends on trusted caller
reporting. Local evidence is operator-writable.

## Inspect, reproduce and remove

- `BUNDLE-SOURCE.json` pins the archive URL and SHA-256. `bundle/` contains its
  exact members, provenance, engine source references, licenses and dependency
  notices. `server/entry.cjs` only adapts Cursor's optional configuration variable.
- Run `python3 tests/acceptance.py` (use `python` on Windows). It verifies every
  release member and exercises the exported plugin command with disposable
  effects. No real accounts, model calls or messages are used.
- Disable/remove the plugin in Cursor, or remove only its local development
  directory. Operator state lives in the private paths you selected and is kept.
  To delete that state, make a separate deliberate backup/removal decision.
- [Source and issues](https://github.com/seanebones-lang/deadbolt) ·
  [Trust guide](https://github.com/seanebones-lang/deadbolt/blob/v1.0.3/docs/TRUST.md) ·
  [Captioned walkthrough](https://www.nexteleven.dev/deadbolt#watch)

No telemetry, model-provider keys, account-wide credentials or paid hosting are
added by this plugin. Your editor subscriptions and downstream services are
separate.
