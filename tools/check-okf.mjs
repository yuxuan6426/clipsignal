import { readFile, readdir, stat } from 'node:fs/promises';
import path from 'node:path';

const root = path.resolve(process.argv[2] ?? '.');
const docs = new Map();
const errors = [];
const decoder = new TextDecoder('utf-8', { fatal: true });

async function collect(dir) {
  for (const entry of await readdir(dir, { withFileTypes: true })) {
    if (entry.name.startsWith('.')) continue;
    const file = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      await collect(file);
    } else if (entry.isFile() && entry.name.endsWith('.md')) {
      docs.set(file, decoder.decode(await readFile(file)).replaceAll('\r\n', '\n'));
    }
  }
}

function splitDocument(text) {
  if (!text.startsWith('---\n')) return { meta: null, body: text };
  const boundary = text.indexOf('\n---\n', 4);
  if (boundary < 0) throw new Error('Unclosed frontmatter');
  const meta = Object.create(null);
  let listKey;
  for (const line of text.slice(4, boundary).split('\n')) {
    if (line.startsWith('  - ') && listKey) {
      meta[listKey].push(JSON.parse(line.slice(4)));
      continue;
    }
    const match = /^([\w-]+):(?: (.+))?$/.exec(line);
    if (!match) throw new Error('Expected YAML key with a JSON-compatible flow value');
    const [, key, value] = match;
    if (Object.hasOwn(meta, key)) throw new Error('Duplicate frontmatter key: ' + key);
    listKey = value === undefined ? key : null;
    meta[key] = listKey ? [] : JSON.parse(value);
  }
  return { meta, body: text.slice(boundary + 5) };
}

function fail(file, message) {
  errors.push(path.relative(root, file) + ' — ' + message);
}

function links(body) {
  const prose = body.replace(/^([~\x60])\1{2,}.*?\n[\s\S]*?^\1{3,}[ \t]*$/gm, '');
  return [...prose.matchAll(/\]\((?:<([^>\n]+)>|([^)\s]+))\)/g)].map(match => match[1] ?? match[2]);
}

async function checkDestination(file, dest) {
  if (/^[a-z][a-z\d+.-]*:/i.test(dest)) {
    if (/^https?:/i.test(dest)) {
      try { new URL(dest); } catch { fail(file, 'Invalid URL: ' + dest); }
    }
    return;
  }
  let target;
  const [resource, fragment] = dest.split('#', 2);
  try {
    const decoded = decodeURIComponent(resource);
    target = decoded
      ? path.resolve(decoded.startsWith('/') ? root : path.dirname(file), decoded.replace(/^\//, ''))
      : file;
  } catch {
    fail(file, 'Invalid path: ' + dest);
    return;
  }
  const relative = path.relative(root, target);
  if (relative === '..' || relative.startsWith('..' + path.sep) || path.isAbsolute(relative)) {
    fail(file, 'Link escapes the knowledge bundle: ' + dest);
    return;
  }
  if (docs.has(target)) {
    if (fragment) {
      const id = decodeURIComponent(fragment);
      const headings = [...docs.get(target).matchAll(/^#{1,6} (.+)$/gm)];
      const found = headings.some(([, heading]) => heading.toLowerCase().replace(/[^\p{L}\p{N} _-]/gu, '').replaceAll(' ', '-') === id);
      if (!found) fail(file, 'Missing heading: ' + dest);
    }
    return;
  }
  if (!(await stat(target).catch(() => null))) fail(file, 'Missing local link target: ' + dest);
}

async function checkConcept(file, meta, body) {
  for (const key of ['type', 'title', 'description']) {
    if (typeof meta?.[key] !== 'string' || !meta[key].trim()) fail(file, 'Missing ' + key);
  }
  if (!Array.isArray(meta?.tags) || !meta.tags.every(v => typeof v === 'string' && v.trim())) {
    fail(file, 'Tags must be a list of non-empty strings');
  }
  for (const at of [meta?.generated?.at, meta?.stale_after, ...(meta?.verified ?? []).map(event => event.at)]) {
    if (at !== undefined && (typeof at !== 'string' || !/^\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2}))?$/.test(at) || !Number.isFinite(Date.parse(at)))) {
      fail(file, 'Invalid RFC 3339 timestamp');
    }
  }
  if (meta?.generated && !/^[^\s:/]+[:/]\S+$/.test(meta.generated.by ?? '')) fail(file, 'Invalid generated actor');
  const sourceIds = new Set();
  if (meta?.sources !== undefined && !Array.isArray(meta.sources)) {
    fail(file, 'Sources must be a list');
    return;
  }
  for (const source of meta?.sources ?? []) {
    if (!source || typeof source.resource !== 'string' || !source.resource.trim()) {
      fail(file, 'Missing source resource');
      continue;
    }
    if (source.id !== undefined) {
      if (!/^[a-z\d][a-z\d-]*$/i.test(source.id) || sourceIds.has(source.id)) fail(file, 'Invalid or duplicate source ID');
      sourceIds.add(source.id);
    }
    await checkDestination(file, source.resource);
  }
  const notes = [...body.matchAll(/^\[\^([\w-]+)\]:/gm)].map(match => match[1]);
  const noteIds = new Set(notes);
  if (notes.length !== noteIds.size) fail(file, 'Duplicate note definition');
  for (const match of body.matchAll(/\[\^([\w-]+)\]/g)) {
    if (!sourceIds.has(match[1]) || !noteIds.has(match[1])) fail(file, 'Unbound footnote: ' + match[1]);
  }
  const index = path.join(path.dirname(file), 'index.md');
  const target = path.basename(file);
  if (!docs.has(index) || !links(docs.get(index)).some(link => link === target || link === './' + target)) {
    fail(file, 'Concept missing from its directory index');
  }
}

await collect(root);
const rootIndex = path.join(root, 'index.md');
if (!docs.has(rootIndex)) fail(rootIndex, 'Missing knowledge bundle index');

for (const [file, text] of docs) {
  try {
    const { meta, body } = splitDocument(text);
    const name = path.basename(file);
    if (name === 'index.md') {
      if (file === rootIndex && (meta?.okf_version !== '0.3' || 'type' in meta)) fail(file, 'Root must declare OKF 0.3');
      if (file !== rootIndex && meta) fail(file, 'Subdirectory index must not have frontmatter');
      if (!/^# /m.test(body) || !/^- \[.+\]\(.+\) - .+/m.test(body)) fail(file, 'Index needs headings and navigation entries');
    } else if (name === 'log.md') {
      const groups = [...body.matchAll(/^## (.+)$/gm)].map(match => match[1]);
      if (meta || !groups.length || groups.some((date, i) => !/^\d{4}-\d{2}-\d{2}$/.test(date) || (i > 0 && groups[i - 1] <= date))) {
        fail(file, 'Log requires date headings in reverse chronological order and no frontmatter');
      }
    } else {
      await checkConcept(file, meta, body);
    }
    for (const dest of links(body)) await checkDestination(file, dest);
  } catch (error) {
    fail(file, error.message);
  }
}

if (errors.length) {
  process.stderr.write(errors.join('\n') + '\n');
  process.exitCode = 1;
} else {
  process.stdout.write('OKF 0.3 project checks passed for ' + docs.size + ' Markdown files.\n');
}
