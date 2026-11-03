import { test } from 'node:test';
import assert from 'node:assert/strict';
import request from 'supertest';
import { createApp } from '../src/app.js';
import { createGoogle, GoogleError, SCOPES } from '../src/google.js';

const config = { baseUrl: 'http://localhost:3000', clientId: 'test-client', clientSecret: 'test-secret', sessionSecret: 'a'.repeat(48) };
function setup(t, overrides = {}, settings = {}) {
  const calls = [];
  const provider = {
    async exchange(code, verifier) { calls.push(['exchange', code, verifier]); return { access_token: 'private-access', refresh_token: 'private-refresh', expires_in: 3600, scope: SCOPES.join(' ') }; },
    async refresh(token) { calls.push(['refresh', token]); return { access_token: 'refreshed-access', expires_in: 3600 }; },
    async revoke(token) { calls.push(['revoke', token]); },
    async get(path, params, token, analytics) {
      calls.push(['get', path, params, token, analytics]);
      if (path === 'channels') return { items: [{ id: 'UC-test', snippet: { title: 'AhangBan', customUrl: '@AhangBan' }, statistics: { viewCount: '123' }, contentDetails: { relatedPlaylists: { uploads: 'UU-test' } } }] };
      if (path === 'playlistItems') return { items: [{ contentDetails: { videoId: 'abc' } }] };
      if (path === 'videos') return { items: [{ id: 'abc', snippet: { title: 'A real video', publishedAt: '2026-01-01T00:00:00Z' }, statistics: { viewCount: '123' } }] };
      if (path === 'reports') return { columnHeaders: [{ name: 'views' }], rows: [[123]] };
      throw new Error('Unexpected path');
    }, ...overrides,
  };
  const app = createApp({ ...config, ...settings }, provider);
  t.after(() => app.locals.close());
  return { app, agent: request.agent(app), calls };
}
async function login(agent) {
  const start = await agent.get('/auth/google').expect(302);
  const state = new URL(start.headers.location).searchParams.get('state');
  return agent.get('/auth/google/callback').query({ code: 'test-code', state }).expect(302);
}

test('setup page works without credentials and reports no connection', async t => {
  const { app } = setup(t, {}, { clientId: '' });
  const response = await request(app).get('/api/status').expect(200);
  assert.equal(response.body.configured, false);
  assert.equal(response.body.connected, false);
  assert.match(response.headers['cache-control'], /no-store/);
  await request(app).get('/').expect(200).expect(/lang="fa"/);
  await request(app).get('/auth/google').expect('Location', '/?notice=setup_required');
});
test('OAuth only requests read-only scopes, exact redirect, PKCE and random state', async t => {
  const { agent } = setup(t);
  const first = await agent.get('/auth/google').expect(302);
  const url = new URL(first.headers.location);
  assert.equal(url.origin, 'https://accounts.google.com');
  assert.equal(url.searchParams.get('scope'), SCOPES.join(' '));
  assert.equal(url.searchParams.get('redirect_uri'), `${config.baseUrl}/auth/google/callback`);
  assert.equal(url.searchParams.get('code_challenge_method'), 'S256');
  assert.ok(url.searchParams.get('code_challenge').length > 32);
  const next = await agent.get('/auth/google');
  assert.notEqual(new URL(next.headers.location).searchParams.get('state'), url.searchParams.get('state'));
});
test('rejects missing, incorrect, cross-session, and replayed state', async t => {
  const { agent, app, calls } = setup(t);
  await agent.get('/auth/google/callback?code=x').expect('Location', '/?notice=invalid_state');
  const start = await agent.get('/auth/google');
  const state = new URL(start.headers.location).searchParams.get('state');
  await request(app).get('/auth/google/callback').query({ code: 'x', state }).expect('Location', '/?notice=invalid_state');
  await agent.get('/auth/google/callback?state=wrong&code=x').expect('Location', '/?notice=invalid_state');
  await agent.get('/auth/google/callback').query({ state, code: 'x' }).expect('Location', '/?notice=invalid_state');
  assert.equal(calls.length, 0);
  await login(agent);
  const before = calls.length;
  await agent.get('/auth/google/callback').query({ state, code: 'x' }).expect('Location', '/?notice=invalid_state');
  assert.equal(calls.length, before);
});
test('denied consent and missing code never exchange tokens', async t => {
  const { agent, calls } = setup(t);
  let start = await agent.get('/auth/google');
  let state = new URL(start.headers.location).searchParams.get('state');
  await agent.get('/auth/google/callback').query({ state, error: 'access_denied' }).expect('Location', '/?notice=consent_denied');
  start = await agent.get('/auth/google'); state = new URL(start.headers.location).searchParams.get('state');
  await agent.get('/auth/google/callback').query({ state }).expect('Location', '/?notice=auth_failed');
  assert.equal(calls.length, 0);
});
test('missing scope rejects connection and revokes the partial grant', async t => {
  const { agent, calls } = setup(t, { async exchange() { return { access_token: 'partial', scope: SCOPES[0] }; } });
  const result = await login(agent);
  assert.equal(result.headers.location, '/?notice=missing_scopes');
  assert.ok(calls.some(c => c[0] === 'revoke' && c[1] === 'partial'));
  assert.equal((await agent.get('/api/status')).body.connected, false);
});
test('connection rotates cookie and keeps tokens off the browser', async t => {
  const { agent } = setup(t);
  const before = await agent.get('/api/status');
  const callback = await login(agent);
  assert.notDeepEqual(callback.headers['set-cookie'], before.headers['set-cookie']);
  const status = await agent.get('/api/status');
  assert.equal(status.body.connected, true);
  assert.doesNotMatch(JSON.stringify(status.body), /private-access|private-refresh|test-secret/);
  assert.match(callback.headers['set-cookie'][0], /HttpOnly/);
  assert.match(callback.headers['set-cookie'][0], /SameSite=Lax/);
});
test('dashboard requires session and has no public token route', async t => {
  const { app } = setup(t);
  await request(app).get('/api/dashboard').expect(401);
  await request(app).get('/api/tokens').expect(404);
});
test('dashboard fetches owned channel, uploads and both analytics reports', async t => {
  const { agent, calls } = setup(t);
  await login(agent);
  const result = await agent.get('/api/dashboard').expect(200);
  assert.equal(result.body.expectedChannel, true);
  assert.equal(result.body.videos[0].id, 'abc');
  assert.equal(result.body.analytics.totals.views, 123);
  assert.equal(result.body.warnings.length, 0);
  assert.doesNotMatch(result.text, /private-access|private-refresh/);
  const queries = calls.filter(c => c[0] === 'get');
  assert.equal(queries.length, 5);
  assert.equal(queries.find(c => c[1] === 'channels')[2].mine, 'true');
  const period = result.body.period;
  assert.equal((Date.parse(period.endDate) - Date.parse(period.startDate)) / 86400000, 27);
  assert.ok(queries.filter(c => c[1] === 'reports').every(c => c[2].ids === 'channel==MINE'));
});
test('analytics errors do not hide channel/video data or fabricate metrics', async t => {
  const { agent } = setup(t, { async get(path, ...args) {
    if (path === 'reports') throw new GoogleError(403, 'forbidden');
    if (path === 'channels') return { items: [{ id: 'other-channel', snippet: { title: 'Other', customUrl: '@Other' }, statistics: {} }] };
    return {};
  } });
  await login(agent);
  const result = await agent.get('/api/dashboard').expect(200);
  assert.equal(result.body.channel.id, 'other-channel');
  assert.equal(result.body.expectedChannel, false);
  assert.equal(result.body.analytics, null);
  assert.deepEqual(result.body.warnings, ['analytics_unavailable']);
});
test('channel missing is an explicit error', async t => {
  const { agent } = setup(t, { async get() { return { items: [] }; } });
  await login(agent);
  await agent.get('/api/dashboard').expect(404).expect({ error: 'no_channel' });
});
test('expired access token refreshes on the server', async t => {
  const { agent, calls } = setup(t, { async exchange() { return { access_token: 'old', refresh_token: 'refresh-only', expires_in: -1, scope: SCOPES.join(' ') }; } });
  await login(agent);
  await agent.get('/api/dashboard').expect(200);
  assert.ok(calls.some(c => c[0] === 'refresh' && c[1] === 'refresh-only'));
  assert.ok(calls.filter(c => c[0] === 'get').every(c => c[3] === 'refreshed-access'));
});
test('revoked refresh grants clear connection and ask to reconnect', async t => {
  const { agent } = setup(t, {
    async exchange() { return { access_token: 'old', refresh_token: 'revoked', expires_in: -1, scope: SCOPES.join(' ') }; },
    async refresh() { throw new GoogleError(400, 'invalid_grant'); },
  });
  await login(agent);
  await agent.get('/api/dashboard').expect(401).expect({ error: 'reconnect_required' });
  assert.equal((await agent.get('/api/status')).body.connected, false);
});
test('logout and disconnect require CSRF; disconnect revokes grant', async t => {
  const { agent, calls } = setup(t);
  await login(agent);
  await agent.post('/api/disconnect').expect(403);
  await agent.post('/api/logout').set('X-CSRF-Token', 'wrong').expect(403);
  assert.equal(calls.filter(c => c[0] === 'revoke').length, 0);
  const { body } = await agent.get('/api/status');
  await agent.post('/api/disconnect').set('X-CSRF-Token', body.csrf).expect(200);
  assert.ok(calls.some(c => c[0] === 'revoke' && c[1] === 'private-refresh'));
  assert.equal((await agent.get('/api/status')).body.connected, false);
  await agent.get('/api/dashboard').expect(401);
});
test('revocation failure is not falsely reported as a disconnected Google account', async t => {
  const { agent } = setup(t, { async revoke() { throw new Error('offline'); } });
  await login(agent);
  const { body } = await agent.get('/api/status');
  await agent.post('/api/disconnect').set('X-CSRF-Token', body.csrf).expect(502).expect({ error: 'revoke_failed' });
  assert.equal((await agent.get('/api/status')).body.connected, true);
  await agent.post('/api/logout').set('X-CSRF-Token', body.csrf).expect(200);
  assert.equal((await agent.get('/api/status')).body.connected, false);
});
test('Google exchange failures do not leak secrets', async t => {
  const { agent } = setup(t, { async exchange() { throw new Error('private-refresh'); } });
  const result = await login(agent);
  assert.equal(result.headers.location, '/?notice=auth_failed');
  assert.doesNotMatch(result.text, /private-refresh/);
});
test('Google client exchanges tokens via POST and sends bearer only to fixed Google endpoint', async () => {
  const calls = [];
  const google = createGoogle({ ...config, redirectUri: config.baseUrl + '/auth/google/callback', fetchImpl: async (url, options) => {
    calls.push([String(url), options]);
    return { ok: true, json: async () => ({ access_token: 'result' }) };
  } });
  await google.exchange('code', 'verifier');
  assert.equal(calls[0][0], 'https://oauth2.googleapis.com/token');
  assert.equal(calls[0][1].method, 'POST');
  assert.equal(calls[0][1].body.get('code_verifier'), 'verifier');
  assert.equal(calls[0][1].body.get('client_secret'), config.clientSecret);
  await google.get('channels', { mine: 'true' }, 'token');
  assert.match(calls[1][0], /^https:\/\/www.googleapis.com\/youtube\/v3\/channels\?/);
  assert.equal(calls[1][1].headers.Authorization, 'Bearer token');
  assert.doesNotMatch(calls[1][0], /token/);
});
test('Google network errors are sanitized', async () => {
  const google = createGoogle({ ...config, fetchImpl: async () => { throw new Error('secret'); } });
  await assert.rejects(google.refresh('secret'), e => e.reason === 'google_unreachable' && !e.message.includes('secret'));
});
test('configuration rejects arbitrary paths and non-HTTPS public origins', () => {
  assert.throws(() => createApp({ ...config, baseUrl: 'http://example.com' }), /requires HTTPS/);
  assert.throws(() => createApp({ ...config, baseUrl: 'https://example.com/wrong' }), /without a path/);
});

test('OAuth state expires after ten minutes and rejects non-ASCII lookalikes safely', async t => {
  const { agent } = setup(t);
  const start = await agent.get('/auth/google');
  const state = new URL(start.headers.location).searchParams.get('state');
  await agent.get('/auth/google/callback').query({ state: 'ی'.repeat(state.length), code: 'x' }).expect('Location', '/?notice=invalid_state');
  const second = await agent.get('/auth/google');
  const secondState = new URL(second.headers.location).searchParams.get('state');
  const future = Date.now() + 600_001;
  t.mock.method(Date, 'now', () => future);
  await agent.get('/auth/google/callback').query({ state: secondState, code: 'x' }).expect('Location', '/?notice=invalid_state');
});
test('HTTPS deployment issues Secure cookies behind trusted proxy and permits preview framing', async t => {
  const { app } = setup(t, {}, { baseUrl: 'https://dashboard.example.com' });
  const response = await request(app).get('/api/status').set('X-Forwarded-Proto', 'https').expect(200);
  assert.match(response.headers['set-cookie'][0], /Secure/);
  assert.match(response.headers['content-security-policy'], /frame-ancestors 'self' https:\/\/arena.ai/);
  assert.equal(response.headers['x-frame-options'], undefined);
  assert.equal(response.body.redirectUri, 'https://dashboard.example.com/auth/google/callback');
});
