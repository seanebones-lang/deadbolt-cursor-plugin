'use strict';

// Cursor owns variable expansion. An unset optional variable sometimes remains
// literal; that exact reserved placeholder is still setup mode. Any supplied
// path goes through the unchanged released launcher's strict validation.
const path = require('node:path');
if (process.argv.length !== 2) {
  process.stderr.write('deadbolt-plugin:unexpected_arguments\n');
  process.exitCode = 1;
} else {
  const value = process.env.DEADBOLT_OPERATOR_CONFIG || '';
  const config = value === '${DEADBOLT_OPERATOR_CONFIG}' ? '' : value;
  const entry = path.resolve(__dirname, '../bundle/server/launcher.cjs');
  process.argv = [process.argv[0], entry, config];
  require(entry);
}
