# DeadBolt for Cursor

**Give agents tools. Keep control.** A free Apache-2.0 local MCP plugin from
[NextEleven](https://www.nexteleven.dev/deadbolt).

Plugin **2.0.0-rc.2** includes the exact published **MCP bundle 2.0.0-rc.2** and
**engine 2.0.0-rc.2**. This is a developer-evaluation prerelease, replacing the
older plugin 1.0.0 candidate that carried engine 1.0.3. Plugin, bundle and engine
versions are separate artifacts even when their version strings match.
Stable promotion awaits independent artifact-pinned retesting.

Node.js 20+ on PATH is required. Included targets: macOS Apple Silicon and Intel,
Linux x64 with glibc, and Windows x64. No Rust build, API key or hosted gate is needed.
No engine is downloaded during plugin installation or startup.

## Read-only setup first

Leave the optional `DEADBOLT_OPERATOR_CONFIG` blank. Cursor discovers exactly two tools:

- `deadbolt_get_integration_guide`: local instructions for stdio, Rust, HTTP or
  Claude Desktop; does not save configuration or grant permission.
- `deadbolt_check_bundle`: reads this host's packaged engine and provenance,
  calculates SHA-256 and reports compatibility and integrity. Does not execute
  the engine, inspect private operator state or test security.

Try: “Verify the DeadBolt bundle and tell me whether protection is active.” Then:
“Get the stdio integration guide and explain its boundaries.”

Setup creates no operator state, starts no downstream server and makes no network
requests. `active_protection` is **false**. Matching a packaged checksum checks
corruption, not independent certification or directory acceptance.

## Load a reviewed local candidate

For **Customize → Plugins → Add → From Local Repository**, select a reviewed
Git checkout of this repository. Its `.cursor-plugin/marketplace.json` indexes
the root plugin. After adding the source, select **Add** beside DeadBolt in the
marketplace view, then return to Manage. Reload the window and confirm DeadBolt
appears under MCPs with two setup tools before prompting the model.

Use an actual Git checkout with a committed HEAD for this repository-import
route. In Cursor 3.24.12, an unpacked folder could appear in the installed list
but failed to resolve `deadbolt@HEAD`; its MCP tools and configuration schema
were unavailable. A successful import notification alone does not prove startup.

Alternatively, for local development, copy the entire repository to
`~/.cursor/plugins/local/deadbolt` using actual files, reload Cursor and inspect
Customize → Plugins and MCP. Review before enabling: the local process runs with
your user's privileges. Marketplace publication requires Cursor review; source
availability does not establish acceptance.

After updating an existing reviewed local copy, verify bundle/engine 2.0.0-rc.2
and back up operator state before upgrading. Do not downgrade to an engine that
ignores newer fields and guarantees. Removing the plugin does not remove its
separate operator state.

If Configure is unavailable, use the
[RC2 editor helper](https://seanebones-lang.github.io/deadbolt/editors-rc2.html)
to add a normal local MCP connection. Do not run both connections against the
same identity. Native MCP connection/model checks with that separate helper do
not establish this plugin's graphical discovery or variable expansion.

## Configure one trusted downstream server

1. Create a private operator-owned state directory outside agent-editable workspaces.
2. Copy `bundle/operator-config.example.json` there. Version 2 requires absolute
   paths, a fresh identity, explicit tools, a future integer Unix-seconds
   `hard_deadline_at`, and an explicit `renewal_mode`. The zero deadline is an
   invalid placeholder. Empty `offline_tools` grants no exceptions.
3. Select `supervisor` when an external trusted supervisor controls liveness.
   Immediately provision and start renewal separately, before the default
   60-second idle TTL expires. The plugin never provisions or receives a renewal
   credential. Follow the [supervision guide](https://github.com/seanebones-lang/deadbolt/blob/main/docs/SUPERVISION.md).
   `activity` is an explicit alternative: live admission renews idle TTL, while
   the fixed deadline never moves. The bundled example selects this alternative
   deliberately; it is not supervisor operation.
4. In **Customize → Plugins → DeadBolt → Configure**, set the optional private
   operator configuration path, save it, and reload the window. Use a distinct
   private configuration filename for each fresh run and verify the actual tool
   list in a new conversation. Valid configuration replaces setup tools with
   the downstream tools. Invalid or expired configuration stops before downstream
   startup; it never falls back to unprotected setup or silently revives a run.
5. Verify disposable allowed and denied effects before connecting accounts.
   Keep the packaged native CLI's policy, approvals, pause, clip, resume and kill
   with the operator. Client permission and DeadBolt admission are separate.

Fresh standalone engine setup defaults to supervision; this launcher requires
an explicit mode. A supervisor can renew idle TTL while the run is still live,
but never past its fixed deadline. When idle TTL or deadline expires, create a
fresh operator-issued identity for a genuinely new run. Resume and restart cannot
resurrect an expired or killed identity. Do not delete state to hide a denial.

This launcher uses **legacy one-shot tool approvals** for classified irreversible
calls. It removes inherited `DEADBOLT_*` variables, including action grant-file
references, before launching its proxy. It does not deliver exact-action grants.
For reviewed argument-bound approvals use the engine's documented Rust, Python
or explicitly configured raw-proxy integration. Do not claim that a broad tool
grant approves the exact arguments of a later call.

## Understand the boundary

Only routed MCP `tools/call` admissions are gated. Startup has a separate liveness
check; arbitrary OS access, other MCP methods, other tools/servers and already
running work are outside this gate. The downstream remains trusted and inherits
its normal user environment. Use OS isolation and executor-owned cancellation
when those are required.

With destination policy set, every routed tool must declare an allowed destination
unless the operator explicitly excepted that tool as offline. A declared foreign
destination remains denied even for an offline-excepted tool. These are trusted
policy declarations, **not OS egress enforcement**. Spend caps use trusted reported
usage. Local state and evidence are operator-writable; private-path and malformed
state checks do not prevent valid edits by the same user.

RC2 returns tool denials as `isError: true` with stable reason/retry metadata.
The model can distinguish `paused`, `killed`, `lease_expired`,
`deadline_exceeded`, `purpose_exceeded` and `store_unavailable` without receiving
operator credentials or private policy. A kill prevents new admissions; it does
not automatically cancel an in-flight tool body.

## Reproduce, troubleshoot and remove

Run `python3 tests/acceptance.py` (`python` on Windows). It downloads the pinned
public archive, checks every vendored member, exercises the exported plugin
command and verifies real disposable marker effects. It uses no model or account.
The suite runs the plugin's exported command; it does not install into a real
Cursor profile or invoke a model. Directory review and model-mediated plugin
acceptance are separate from these protocol checks. Native MCP connection/model
checks with the separate bundle are different evidence.

If startup fails, validate the configuration version, absolute paths, tool lists,
future fixed deadline and live identity with the operator CLI. Diagnostics avoid
printing private paths, arguments and credentials. A missing or unsafe store fails
closed. Changing a deadline or mode of an existing run is refused.

Disable/remove the plugin in Cursor, or remove its local development folder. Operator state is retained at the paths you selected; back it up
or remove it deliberately as a separate action. Do not commit private config,
credentials or state to this repository.

[Engine source and issues](https://github.com/seanebones-lang/deadbolt) ·
[Installation and migration](https://github.com/seanebones-lang/deadbolt/blob/main/docs/INSTALL.md) ·
[Trust boundaries](https://github.com/seanebones-lang/deadbolt/blob/main/docs/TRUST.md) ·
[Captioned walkthrough](https://www.nexteleven.dev/deadbolt#watch)

## Privacy Policy

The plugin itself adds no telemetry, network calls, account connections or model
provider credentials. Read-only setup reads only bundled metadata, documentation
and this host's packaged executable for checksum verification. It creates no
operator state and starts no downstream server.

Configured mode reads the operator-selected private JSON configuration, launches
that trusted local stdio server and passes requests/responses between it and the
Cursor client. Tool names, arguments and responses may contain personal data.
The engine keeps leases, operator approvals and audit events in the private
SQLite/event paths you select. These local records are operator-writable and are
not tamper-proof; their retention is under the operator's control. Removing the
plugin does not remove those records. Back up or delete them separately when you
deliberately choose to do so.

DeadBolt does not send data to NextEleven. Cursor's model/service data handling
and the downstream server's network activity and retention follow their own
policies. The trusted downstream process inherits its normal local environment
and user privileges; this plugin does not sanitize that environment or sandbox
its network access. Review it before connecting accounts or personal data.
No services are connected by default. Do not commit private configuration,
credentials or local operator records to the plugin repository.

Support and privacy questions: **nextelevenstudios@gmail.com**.
This developer tool is intended for adult operators. No paid hosting is added;
Cursor subscriptions and downstream services are separate.
