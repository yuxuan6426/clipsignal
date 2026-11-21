import { readFileSync, existsSync } from 'node:fs';
import { dirname, resolve } from 'node:path';

const [template, mapping, ...extra] = process.argv.slice(2);
if (!template || !mapping || extra.length) throw new Error('Usage: node tools/draft-plan.mjs TEMPLATE MAP');
const load = file => JSON.parse(readFileSync(file, 'utf8').replace(/^\uFEFF/, ''));
const plan = load(template);
const sources = load(mapping);
for (const track of plan.tracks.filter(track => track.type === 'video')) {
  for (const clip of track.segments) {
    if (!Object.hasOwn(sources, clip.path)) throw new Error('Unmapped media ID: ' + clip.path);
    const source = resolve(dirname(resolve(mapping)), sources[clip.path]);
    if (!existsSync(source)) throw new Error('Missing mapped media: ' + clip.path);
    clip.path = source;
  }
}
console.log(JSON.stringify(plan, null, 2));
