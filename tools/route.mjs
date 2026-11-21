import { readFileSync } from 'node:fs';
import { pathToFileURL } from 'node:url';

export function nextSteps(checks) {
  const routes = { missing: 'setup', broken: 'repair', 'needs-auth': 'pending', unverified: 'verify' };
  if (!Array.isArray(checks)) throw new TypeError('Expected checks array');
  return checks.flatMap(({ id, state }) => {
    if (state === 'ready') return [];
    if (!Object.hasOwn(routes, state)) throw new Error('Unknown check state: ' + state);
    return [{ id, action: routes[state] }];
  });
}

export function canRetry({ authorized, receipt }) {
  return authorized === true && receipt === 'confirmed-not-applied';
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const [action, input] = process.argv.slice(2);
  const plan = JSON.parse(readFileSync(action === '--retry' ? input : action, 'utf8').replace(/^\uFEFF/, ''));
  const result = action === '--retry' ? { eligible: canRetry(plan) } : { actions: nextSteps(plan.checks) };
  console.log(JSON.stringify(result, null, 2));
}
