import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const roles = new Set(['repair', 'fleet', 'distributor', 'manufacturer', 'trader', 'unknown']);
const relevantRoles = new Set(['repair', 'fleet', 'distributor']);
const intentTypes = new Set(['explicit-inquiry', 'opt-in', 'rfq']);

function businessEvidence(value) {
  if (value?.status === 'confirmed' && publicWeb(value.source)) {
    return { status: 'confirmed', source: value.source };
  }
  return { status: 'unknown' };
}

function companyDomain(value) {
  if (typeof value !== 'string' || !value.trim()) return '';
  try {
    const source = value.includes('://') ? value : 'https://' + value;
    const address = new URL(source);
    return address.protocol === 'https:' || address.protocol === 'http:'
      ? address.hostname.toLowerCase().replace(/^www\./, '').replace(/\.$/, '')
      : '';
  } catch {
    return '';
  }
}

function publicWeb(value) {
  try {
    const parsed = new URL(value);
    return ['https:', 'http:'].includes(parsed.protocol) && !parsed.username && !parsed.password;
  } catch {
    return false;
  }
}

export function triage(items) {
  if (!Array.isArray(items)) throw new TypeError('Expected an array of sample events');
  const accounts = new Map();
  const visibleEvents = new Set();

  for (const event of items) {
    if (!event || typeof event.id !== 'string' || !event.id.trim()) {
      throw new TypeError('Each sample event needs an id');
    }
    if (visibleEvents.has(event.id)) continue;
    visibleEvents.add(event.id);
    const domain = companyDomain(event.companySite);
    // A profile signal is never a company identifier.
    const key = domain || 'unresolved:' + event.id;
    const account = accounts.get(key) ?? {
      key, company: domain ? event.company || domain : null, roleEvidence: [], signals: [], allowedIntents: [],
    };
    if (domain && roles.has(event.role) && publicWeb(event.officialEvidence)
      && !account.roleEvidence.some(fact => fact.role === event.role && fact.url === event.officialEvidence)) {
      account.roleEvidence.push({ role: event.role, url: event.officialEvidence });
    }
    const signal = {
      id: event.id,
      kind: event.signal || 'observation',
      observedAt: event.observedAt || null,
      source: publicWeb(event.source) ? event.source : null,
    };
    if (event.platform === 'x' || event.platform === 'facebook') signal.platform = event.platform;
    if ('profile' in event && publicWeb(event.profile)) signal.profile = event.profile;
    if ('contentTime' in event && typeof event.contentTime === 'string') signal.contentTime = event.contentTime;
    if ('productFit' in event) signal.productFit = businessEvidence(event.productFit);
    if ('importCapability' in event) signal.importCapability = businessEvidence(event.importCapability);
    if (publicWeb(event.businessContact)) signal.businessContact = event.businessContact;
    account.signals.push(signal);
    if (intentTypes.has(event.signal) && publicWeb(event.source) && event.businessUse === true) {
      account.allowedIntents.push(event.id);
    }
    accounts.set(key, account);
  }

  return [...accounts.values()].map(account => {
    const knownRoles = [...new Set(account.roleEvidence.map(fact => fact.role).filter(role => role !== 'unknown'))];
    const role = knownRoles.length === 1 ? knownRoles[0] : 'unknown';
    let state = '待核';
    let next = '核实企业身份、角色与主动需求';
    if (knownRoles.length > 1) {
      next = '核对互相冲突的主体角色证据';
    } else if (role === 'manufacturer' || role === 'trader') {
      state = '非终端分流';
      next = '交由合作或竞品记录';
    } else if (relevantRoles.has(role) && account.allowedIntents.length) {
      state = role === 'distributor' ? '渠道交接' : '可交接';
      next = '业务员核对车型、车桥或件号、数量及报价依据';
    } else if (relevantRoles.has(role)) {
      next = '保留企业候选，等待主动需求';
    }
    return { ...account, role, state, next };
  });
}

if (process.argv[2] === '--self-test') {
  const fleet = {id:'fleet-public',company:'Example Parts',companySite:'https://candidate.example',
    role:'repair',officialEvidence:'https://candidate.example/service',signal:'company-reference',
    source:'https://candidate.example/service'};
  const watch = {id:'replay-unlinked',signal:'repeat-comment',
    source:'https://www.youtube.com/watch?v=MFt7VYZPaxc'};
  const ready = {id:'fake-rfq',company:'Synthetic repair shop',companySite:'https://repair.example',
    role:'repair',officialEvidence:'https://repair.example/about',signal:'rfq',
    businessUse:true,source:'https://repair.example/forms/rfq'};
  const supplier = {id:'fake-supplier',companySite:'https://supplier.example',role:'manufacturer',
    officialEvidence:'https://supplier.example/about',signal:'rfq',businessUse:true,source:'https://supplier.example/rfq'};
  const conflict = { ...ready, id:'fake-conflict', role:'trader' };
  const clean = triage([fleet, watch, ready, ready, supplier]);
  assert.deepEqual(clean.map(a => a.state), ['待核', '待核', '可交接', '非终端分流']);
  assert.equal(clean[2].signals.length, 1);
  assert.equal(triage([ready, conflict])[0].state,'待核');
  assert.equal(triage([{...ready,role:'distributor'}])[0].state,'渠道交接');
  assert.equal(triage([{...ready,businessUse:false}])[0].state,'待核');
  assert.equal(triage([{...ready,officialEvidence:null}])[0].state,'待核');
  assert.equal(triage([{...ready,source:'file:///local'}])[0].state,'待核');
  const discovery = [
    {...fleet, id:'x-seed', platform:'x', observedAt:'2026-11-21T18:09:56+08:00',
      productFit:{status:'confirmed',source:fleet.officialEvidence}, importCapability:{status:'confirmed'}},
    {...fleet, id:'facebook-seed', platform:'facebook', observedAt:'2026-11-21T18:09:56+08:00'},
  ];
  const [candidate] = triage(discovery);
  assert.equal(candidate.state, '待核');
  assert.deepEqual(candidate.signals.map(signal => signal.platform), ['x', 'facebook']);
  assert.equal(candidate.roleEvidence.length, 1);
  assert.equal(candidate.signals[0].productFit.status, 'confirmed');
  assert.equal(candidate.signals[0].importCapability.status, 'unknown');
  console.log('通过：真实企业候选、回放弱信号、合成询盘、跨渠道重复、角色冲突、用途与来源边界。');
} else if (process.argv[2]) {
  console.log(JSON.stringify(triage(JSON.parse(readFileSync(process.argv[2], 'utf8').replace(/^\uFEFF/, ''))), null, 2));
}
