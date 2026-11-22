import { copyFileSync, lstatSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';

const root = fileURLToPath(new URL('../', import.meta.url));
if (!process.argv[2]) throw new Error('Usage: node tools/build-pages.mjs <new-output-directory>');
const out = resolve(process.argv[2]);
const names = ['index.html', 'guide/index.html', 'style.css', 'script.js'];
const images = JSON.parse(readFileSync(join(root, 'assets/showcase/selected.json'), 'utf8'));
const byId = new Map();
const escape = value => value.replace(/[&"<>]/g, char => ({ '&': '&amp;', '"': '&quot;', '<': '&lt;', '>': '&gt;' })[char]);
for (const image of images) {
  const { id, file, alt, sha256, width, height } = image;
  if (!/^(case-[a-z]+|scene-\d\d|diagram-[a-z]+)$/.test(id) || byId.has(id)
    || file !== id + '.webp' || typeof alt !== 'string' || !alt.trim()
    || !/^[a-f\d]{64}$/.test(sha256)
    || !Number.isSafeInteger(width) || width < 1 || !Number.isSafeInteger(height) || height < 1) throw new Error('Invalid selected artwork entry');
  const source = join(root, 'assets/showcase', file);
  if (!lstatSync(source).isFile()
    || createHash('sha256').update(readFileSync(source)).digest('hex') !== sha256) {
    throw new Error('Artwork file mismatch: ' + file);
  }
  byId.set(id, image);
}
mkdirSync(out);
for (const name of names) {
  const source = join(root, 'site', name);
  const dest = join(out, name);
  mkdirSync(dirname(dest), { recursive: true });
  if (!name.endsWith('.html')) {
    copyFileSync(source, dest);
    continue;
  }
  const prefix = name.includes('/') ? '../' : './';
  const page = readFileSync(source, 'utf8').replace(/(<(?:article|div)\b[^>]+\bdata-art="([^"]+)"[^>]*>)/g,
    (match, tag, id) => {
      const image = byId.get(id);
      if (!image) return match;
      const priority = id === 'case-kooying' ? 'fetchpriority="high"' : 'loading="lazy"';
      const size = ' width="' + image.width + '" height="' + image.height + '"';
      return tag + '<img class="art" ' + priority + size + ' src="' + prefix + 'assets/showcase/' + image.file
        + '" alt="' + escape(image.alt) + '">';
    });
  const gallery = page.replace(/<article class="scene-tile" data-art="([^"]+)">/g,
    (match, id) => byId.has(id) ? match : match.slice(0, -1) + " hidden>");
  const rendered = [...byId.keys()].some(id => id.startsWith("scene-"))
    ? gallery.replace('class="shell block scenes" hidden', 'class="shell block scenes"')
    : gallery;
  writeFileSync(dest, rendered);
}
for (const image of images) {
  const rel = join('assets/showcase', image.file);
  mkdirSync(dirname(join(out, rel)), { recursive: true });
  copyFileSync(join(root, rel), join(out, rel));
}
writeFileSync(join(out, '.nojekyll'), '');
console.log('Built two ClipSignal pages with ' + byId.size + ' selected images');