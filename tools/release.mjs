import { readFileSync, writeFileSync, lstatSync, existsSync, mkdirSync, copyFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const manifest = join(root, 'delivery.json');
const requirements = [
  { id: 'windows-codex', kind: 'host', handling: 'Windows x64, Codex and the recipient Chrome and Gmail connections.' },
  { id: 'windows-tools', kind: 'host', handling: 'Git Bash, PowerShell 7, Miniconda, Node.js and Dev-C++ x64 GCC; run setup.ps1 -Check.' },
  { id: 'wechat', kind: 'rebuild', handling: 'Create Python 3.13 and install the module requirement pins via setup.ps1 -Apply -Flow wechat.' },
  { id: 'upstream-media', kind: 'rebuild', handling: 'Use recipient installs of douyin-agent and jianying-draft-collab with their corresponding delivery and environment locks.' },
  { id: 'jianying', kind: 'host', handling: 'Recipient Jianying Pro, native probe and draft paths.' },
  { id: 'services', kind: 'configure', handling: 'Set recipient credentials and verify each authorized service using docs/setup.md.' },
  { id: 'media', kind: 'input', handling: 'Supply authorized footage or generate synthetic testing inputs.' },
];

function staged() {
  return execFileSync('git', ['ls-files', '-z'], { cwd: root, encoding: 'utf8' })
    .split('\0').filter(file => file && file !== 'delivery.json').sort();
}

function inspect(files) {
  if (!Array.isArray(files) || !files.length || [...new Set(files)].length !== files.length) {
    throw new Error('Invalid or duplicate release files');
  }
  for (const file of files) {
    if (!/^[a-z0-9_.-]+(?:\/[a-z0-9_.-]+)*$/i.test(file)
      || file.split('/').some(part => ['.', '..', '.git', '.local'].includes(part.toLowerCase()))
      || /(?:^|\/)\.env(?!\.example$)|\.(?:aac|mp3|mp4|sqlite3?|db|pem|pfx)$/i.test(file)) {
      throw new Error('Disallowed release path: ' + file);
    }
    const path = join(root, file);
    if (!lstatSync(path).isFile()) throw new Error('Not a plain file: ' + file);
    if (/\.(md|html|json|toml|mjs|js|py|ps1|sh|cmd|ya?ml|txt|example)$/i.test(file)) {
      const text = readFileSync(path, 'utf8');
      if (/(?:[a-z]:[/\\](?:users[/\\]|intercity-hack-2026|jianying-draft-collab|wechat-channels-local)|\.\u672c\u673a\u8d44\u6599)/i.test(text)) {
        throw new Error('Machine-specific path: ' + file);
      }
      if (/-----BEGIN (?:OPENSSH |RSA |EC )?PRIVATE KEY-----|\b(?:gh[pousr]_[a-z0-9]{30,}|sk-[a-z0-9_-]{32,})\b/i.test(text)
        || /^\s*(?:VOLC_AGENT_API_KEY|BOCHA_API_KEY|YUNFU_MCP_TOKEN|SOCIALDATAX_API_KEY)=[ \t]*['"]?[a-z0-9_-]{16,}/im.test(text)) {
        throw new Error('Possible secret in ' + file);
      }
    }
  }
}

const [action, destination] = process.argv.slice(2);
if (action === 'manifest') {
  const files = staged();
  inspect(files);
  writeFileSync(manifest, JSON.stringify({ schema_version: 1, name: 'clipsignal', version: '0.1.0', files, requirements }, null, 2) + '\n');
  console.log(files.length + ' files declared');
} else if (action === 'check' || action === 'export') {
  const delivery = JSON.parse(readFileSync(manifest, 'utf8'));
  inspect(delivery.files);
  if (existsSync(join(root, '.git')) && JSON.stringify(delivery.files) !== JSON.stringify(staged())) {
    throw new Error('Git index and delivery list differ');
  }
  if (action === 'export') {
    if (!destination) throw new Error('Pass a new destination directory.');
    const target = resolve(destination);
    mkdirSync(target);
    for (const file of [...delivery.files, 'delivery.json']) {
      const out = join(target, file);
      mkdirSync(dirname(out), { recursive: true });
      copyFileSync(join(root, file), out);
    }
  }
  console.log('Release checks passed for ' + delivery.files.length + ' files');
} else {
  throw new Error('Usage: node tools/release.mjs {manifest|check|export [new-directory]}');
}
