import { readFileSync } from 'node:fs';
import { parseEnv } from 'node:util';

let configured = {};
try {
  configured = parseEnv(readFileSync(new URL('../.local/config/services.env', import.meta.url), 'utf8'));
} catch (error) {
  if (error.code !== 'ENOENT') {
    console.error('Cloudbat: cannot read the project configuration.');
    process.exit(1);
  }
}
const token = (process.env.YUNFU_MCP_TOKEN ?? configured.YUNFU_MCP_TOKEN ?? '').trim();
if (!/^[\x21-\x7e]+$/.test(token)) {
  console.error('Cloudbat: configure YUNFU_MCP_TOKEN.');
  process.exit(1);
}
console.log(JSON.stringify({ Authorization: 'Bearer ' + token }));
