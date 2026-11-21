import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const args = process.argv.slice(2);
const pythonFlag = args.indexOf('--python');
const python = pythonFlag < 0 ? null : args[pythonFlag + 1];
const quote = JSON.stringify;
const sections = [];
if (args.includes('--statusline')) {
  if (!python) throw new Error('Pass --python with the recipient Python executable.');
  sections.push([
    '[features]', 'tui_extensions_statusline = true', '',
    '[mcp_servers.clipsignal-status]',
    'command = ' + quote(resolve(python)),
    'args = ' + quote(['-u', join(root, 'tools', 'status.py')]),
    'cwd = ' + quote(root),
  ].join('\n'));
}
if (args.includes('--cloudbat')) {
  const script = join(root, 'tools', 'cloudbat.mjs').replaceAll('\\', '/');
  sections.push([
    '[mcp_servers.saas]',
    'url = "https://ai.telrobot.top/cli/mcp"',
    'http_headers_helper = ' + quote('node "' + script + '"'),
  ].join('\n'));
}
if (!sections.length) throw new Error('Choose --statusline or --cloudbat.');
console.log(sections.join('\n\n'));
