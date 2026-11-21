import { mkdirSync, writeFileSync, renameSync } from 'node:fs';
import { randomUUID } from 'node:crypto';

const [thread, module, phase, state, pending] = process.argv.slice(2);
const fields = [
  [thread, /^(?!workspace$)[a-zA-Z0-9_-]{1,100}$/],
  [module, /^(setup|media|edit|leads|wechat|publish|outreach|repair|memory)$/],
  [phase, /^(prepare|run|verify|done)$/],
  [state, /^(ready|working|passed|needs-auth|blocked)$/],
];
if (fields.some(([value, pattern]) => !value || !pattern.test(value))
  || (pending && !/^(setup|auth|receipt|review)$/.test(pending))) {
  throw new Error('Usage: node tools/progress.mjs THREAD MODULE PHASE STATE [PENDING]');
}
const folder = new URL('../.local/runs/', import.meta.url);
mkdirSync(folder, { recursive: true });
const staging = new URL('.' + randomUUID() + '.tmp', folder);
writeFileSync(staging, JSON.stringify({ module, phase, state, pending }), 'utf8');
renameSync(staging, new URL(thread + '.json', folder));
