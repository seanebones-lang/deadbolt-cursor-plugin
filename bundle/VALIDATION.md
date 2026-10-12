# Bundle 1.1.0 validation

Engine is published stable v1.0.3; packaging source is 027dce7. Four-platform installed-bundle CI passed 25 cases per host, including optional setup in ordinary and imported/bridged Node and the protected allow/deny/approval/pause/clip/kill/expiry/storage checks. JSON reports are in validation/.

Claude Desktop 2.19675.1 on macOS ARM64 ran both actual setup tools with blank configuration. Bundle verification returned checksum_matches=true and active_protection=false. Applying a disposable operator configuration replaced the setup tools with its three downstream tools. The extension was removed after testing. This graphical test used identical runtime files; final packaging adds these validation reports and provenance. No real accounts were connected. Prior 1.0.1 graphical testing exercised allow/deny dummy effects; current cross-platform stdio testing covers those effects again.

Setup-mode metadata describes only actual read-only setup tools. Configured mode uses generated downstream tools and explicit policy. A score from a registry does not constitute independent security certification.
