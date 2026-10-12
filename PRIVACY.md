# DeadBolt Cursor Plugin Privacy Policy

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
and user privileges. DeadBolt removes its credentials and state-location environment
variables before starting the downstream server; other application variables remain
inherited. It does not sandbox network access. Review it before connecting accounts or personal data.
No services are connected by default. Do not commit private configuration,
credentials or local operator records to the plugin repository.

Support and privacy questions: **nextelevenstudios@gmail.com**.
This developer tool is intended for adult operators. No paid hosting is added;
Cursor subscriptions and downstream services are separate.
