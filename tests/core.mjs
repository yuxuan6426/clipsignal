import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdtempSync, readFileSync, writeFileSync, unlinkSync, rmdirSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { fileURLToPath } from 'node:url';
import { join } from 'node:path';
import test from 'node:test';
import { canRetry, nextSteps } from '../tools/route.mjs';

const root = fileURLToPath(new URL('../', import.meta.url));

test('routes missing, broken, dependent authorization and read-only checks', () => {
  const checks = [
    { id: 'media', state: 'missing' }, { id: 'edit', state: 'broken' },
    { id: 'cloudbat', state: 'needs-auth' }, { id: 'chrome', state: 'unverified' },
    { id: 'node', state: 'ready' },
  ];
  assert.deepEqual(nextSteps(checks).map(item => item.action), ['setup', 'repair', 'pending', 'verify']);
  assert.deepEqual(nextSteps(checks.map(check => ({ ...check, state: 'ready' }))), []);
});

test('does not repeat actions until the previous attempt is confirmed not applied', () => {
  for (const receipt of ['unknown', 'sent', 'published', 'connected', null]) {
    assert.equal(canRetry({ authorized: true, receipt }), false);
  }
  assert.equal(canRetry({ authorized: true, receipt: 'confirmed-not-applied' }), true);
  assert.equal(canRetry({ authorized: false, receipt: 'confirmed-not-applied' }), false);
});

test('lead CLI accepts BOM input and merges separate platform evidence', () => {
  const dir = mkdtempSync(join(tmpdir(), 'clipsignal-'));
  const file = join(dir, 'events.json');
  try {
    writeFileSync(file, '\uFEFF' + readFileSync(join(root, 'examples/leads.json'), 'utf8'));
    const output = spawnSync(process.execPath, ['tools/leads.mjs', file], { cwd: root, encoding: 'utf8' });
    assert.equal(output.status, 0, output.stderr);
    const data = JSON.parse(output.stdout);
    assert.equal(data.length, 1);
    assert.equal(data[0].signals.length, 2);
    assert.equal(data[0].roleEvidence.length, 1);
    assert.deepEqual(data[0].allowedIntents, []);
  } finally {
    unlinkSync(file);
    rmdirSync(dir);
  }
});

test('Cloudbat configuration resolves the caller copy without including a credential', () => {
  const result = spawnSync(process.execPath, ['tools/mcp-config.mjs', '--cloudbat'], { cwd: root, encoding: 'utf8' });
  assert.equal(result.status, 0, result.stderr);
  assert.ok(result.stdout.includes(join(root, 'tools/cloudbat.mjs').replaceAll('\\', '/')));
  assert.ok(!result.stdout.includes('YUNFU_MCP_TOKEN'));
});
