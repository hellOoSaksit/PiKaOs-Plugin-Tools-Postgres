/* A plugin's screen may only use keys its OWN packs ship. Anything else is a bet on another plugin
   being installed: DbChoice used to call t('firstadmin.errNetwork') back when that key sat in Core's
   Base packs — the moment the auth plugin took its strings with it, a postgres-without-auth install
   would have rendered the raw key at the operator mid-install. This pins the rule at the source. */
import { readFileSync } from 'node:fs';
import { it, expect } from 'vitest';
import en from './i18n/en-formal.json';
import th from './i18n/th-formal.json';
import ja from './i18n/ja-formal.json';

const PACKS = [['en', en], ['th', th], ['ja', ja]];
const SRC = readFileSync(new URL('./DbChoice.jsx', import.meta.url), 'utf8');
const USED = [...SRC.matchAll(/\bt\(\s*'([^']+)'/g)].map((m) => m[1]);

it('DbChoice references at least the keys we expect (the scan works)', () => {
  expect(USED).toContain('dbchoice.failed');
  expect(USED.length).toBeGreaterThan(5);
});

it('every key DbChoice uses is one this plugin owns — no borrowing from another plugin', () => {
  const foreign = [...new Set(USED)].filter((k) => !k.startsWith('dbchoice.'));
  expect(foreign, `DbChoice uses keys it does not own: ${foreign.join(', ')}`).toEqual([]);
});

it('every pack defines every key DbChoice uses', () => {
  for (const [name, pack] of PACKS)
    for (const k of new Set(USED)) expect(pack.translations[k], `${name} missing ${k}`).toBeTruthy();
});
