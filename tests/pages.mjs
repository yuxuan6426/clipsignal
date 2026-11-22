import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdtempSync, readFileSync, readdirSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';

const root = fileURLToPath(new URL('../', import.meta.url));

test('publishes only the two pages, their shared code and approved illustrations', () => {
  const scratch = mkdtempSync(join(tmpdir(), 'clipsignal-pages-'));
  const out = join(scratch, 'clipsignal');
  try {
    const result = spawnSync(process.execPath, ['tools/build-pages.mjs', out], { cwd: root, encoding: 'utf8' });
    assert.equal(result.status, 0, result.stderr);
    const artwork = JSON.parse(readFileSync(join(root, 'assets/showcase/selected.json'), 'utf8'));
    const expected = ['.nojekyll', 'guide/index.html', 'index.html', 'script.js', 'style.css',
      ...artwork.map(image => 'assets/showcase/' + image.file)];
    const actual = readdirSync(out, { recursive: true, withFileTypes: true })
      .filter(item => item.isFile())
      .map(item => join(item.parentPath, item.name).slice(out.length + 1).replaceAll('\\', '/'));
    assert.deepEqual(actual.sort(), expected.sort());
    const index = readFileSync(join(out, 'index.html'), 'utf8');
    const guide = readFileSync(join(out, 'guide/index.html'), 'utf8');
    assert.match(index, /href="\.\/guide\/"/);
    assert.match(guide, /href="\.\.\/style\.css"/);
    if (artwork.some(image => image.id === 'scene-01')) assert.match(index, /\.\/assets\/showcase\/scene-01\.webp/);
    for (const image of artwork) assert.ok(guide.includes('../assets/showcase/' + image.file));
  } finally {
    rmSync(scratch, { recursive: true });
  }
});

test('Pages publishes from public main only', () => {
  const workflow = readFileSync(join(root, '.github/workflows/pages.yml'), 'utf8');
  assert.equal((workflow.match(/if: github\.event\.repository\.private == false && github\.ref == 'refs\/heads\/main'/g) ?? []).length, 2);
  assert.match(workflow, /gh api "repos\/\$GITHUB_REPOSITORY" --jq \.private/);
  assert.match(workflow, /path: dist-pages/);
});