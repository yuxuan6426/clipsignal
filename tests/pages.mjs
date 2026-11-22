import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdtempSync, readFileSync, readdirSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';

const root = fileURLToPath(new URL('../', import.meta.url));

test('publishes only the three pages, their code and approved media', () => {
  const scratch = mkdtempSync(join(tmpdir(), 'clipsignal-pages-'));
  const out = join(scratch, 'clipsignal');
  try {
    const result = spawnSync(process.execPath, ['tools/build-pages.mjs', out], { cwd: root, encoding: 'utf8' });
    assert.equal(result.status, 0, result.stderr);
    const artwork = JSON.parse(readFileSync(join(root, 'assets/showcase/selected.json'), 'utf8'));
    const demo = readFileSync(join(out, 'demo/index.html'), 'utf8');
    const chapters = [...demo.matchAll(/id="((?:booth|pitch)-[^"]+)" data-seconds="(\d+)"[^>]*>([\s\S]*?)<\/section>/g)];
    assert.equal(chapters.length, 17);
    assert.equal(new Set(chapters.map(([, id]) => id)).size, chapters.length);
    const timeFor = mode => chapters.filter(([, id]) => id.startsWith(mode + '-'))
      .reduce((time, [, , seconds]) => time + Number(seconds), 0);
    const booth = chapters.filter(([, id]) => id.startsWith('booth-'));
    assert.deepEqual(booth.map(([, , seconds]) => Number(seconds)), [2, 3, 3, 3, 3, 3, 3, 4]);
    assert.ok(booth.every(([, , , content]) => content.includes('<img class="art"')));
    assert.equal(timeFor('booth'), 24);
    assert.equal(timeFor('pitch'), 240);
    for (const [, id, seconds, content] of chapters) {
      const cues = [...content.matchAll(/data-cue="(\d+)"/g)].map(([, at]) => Number(at));
      assert.equal(cues[0], 0, 'First subtitle for ' + id);
      assert.ok(cues.every((at, i) => at < Number(seconds) * 1000 && (!i || cues[i - 1] < at)), 'Subtitle order for ' + id);
      const voice = readFileSync(join(out, 'demo/media', id + '.m4a'));
      assert.equal(voice.subarray(4, 8).toString(), 'ftyp', 'Playable asset container for ' + id);
    }
    const expected = ['.nojekyll', 'guide/index.html', 'index.html', 'script.js', 'style.css',
      'demo/index.html', 'demo/demo.js', 'demo/demo.css', 'demo/media/pitch-qr.png',
      ...chapters.map(([, id]) => 'demo/media/' + id + '.m4a'),
      ...artwork.map(image => 'assets/showcase/' + image.file)];
    const actual = readdirSync(out, { recursive: true, withFileTypes: true })
      .filter(item => item.isFile())
      .map(item => join(item.parentPath, item.name).slice(out.length + 1).replaceAll('\\', '/'));
    assert.deepEqual(actual.sort(), expected.sort());
    const index = readFileSync(join(out, 'index.html'), 'utf8');
    const guide = readFileSync(join(out, 'guide/index.html'), 'utf8');
    assert.match(index, /href="\.\/guide\/"/);
    assert.match(guide, /href="\.\.\/style\.css"/);
    assert.match(index, /href="\.\/demo\/"/);
    assert.ok(guide.includes('href="../demo/?mode=pitch"'));
    assert.ok(demo.includes('href="?mode=booth"') && demo.includes('href="?mode=pitch"'));
    assert.ok(demo.includes('src="./media/pitch-qr.png"') && demo.includes('../assets/showcase/case-kooying.webp'));
    assert.match(index, /fetchpriority="high"[^>]+src="\.\/assets\/showcase\/case-kooying\.webp"/);
    for (const image of artwork) {
      assert.ok(index.includes('./assets/showcase/' + image.file) || guide.includes('../assets/showcase/' + image.file));
    }
    assert.match(guide, /id="edit"/);
    assert.match(guide, /id="leads"/);
  } finally {
    rmSync(scratch, { recursive: true });
  }
});

test('Pages publishes only when manually requested on public main', () => {
  const workflow = readFileSync(join(root, '.github/workflows/pages.yml'), 'utf8');
  assert.match(workflow, /^on:\s*\n  workflow_dispatch:\s*\n\s*permissions:/m);
  assert.equal((workflow.match(/if: github\.event\.repository\.private == false && github\.ref == 'refs\/heads\/main'/g) ?? []).length, 2);
  assert.match(workflow, /gh api "repos\/\$GITHUB_REPOSITORY" --jq \.private/);
  assert.match(workflow, /path: dist-pages/);
});
