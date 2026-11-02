import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { JSDOM } from 'jsdom';

const html = readFileSync(new URL('../public/index.html', import.meta.url), 'utf8');
const script = readFileSync(new URL('../public/app.js', import.meta.url), 'utf8');
const fixture = {
  channel: { title: '<script>not executable</script>', handle: '@AhangBan', id: 'UC-test', thumbnail: 'https://evil.example/tracker' },
  expectedChannel: true, period: { startDate: '2026-10-01', endDate: '2026-10-28' },
  analytics: { totals: { views: 100, estimatedMinutesWatched: 120, subscribersGained: 5, subscribersLost: 2, averageViewDuration: 20 },
    daily: [{ day: '2026-10-01', views: 40 }, { day: '2026-10-28', views: 60 }] },
  videos: [{ id: 'test-video', title: '<img src=x onerror=alert(1)>', publishedAt: '2026-10-01', thumbnail: 'https://i.ytimg.com/vi/test/mqdefault.jpg', statistics: { viewCount: '50' } }], warnings: [],
};
async function setup(t, { connected = false, configured = false, data = fixture } = {}) {
  const dom = new JSDOM(html, { url: 'https://dashboard.example/', runScripts: 'outside-only' });
  t.after(() => dom.window.close());
  const calls = [];
  dom.window.fetch = async path => {
    calls.push(path);
    return { ok: true, json: async () => path === '/api/status' ? { connected, configured, csrf: 'test-csrf' } : data };
  };
  dom.window.eval(script);
  // Flush initial status -> dashboard -> render promise chain without network or browser timers.
  await new Promise(resolve => setImmediate(resolve));
  return { window: dom.window, document: dom.window.document, calls };
}
test('unconfigured UI shows no fabricated metrics and routes connect to setup', async t => {
  const { document, calls } = await setup(t);
  assert.equal(document.getElementById('metric-views').textContent, '—');
  assert.deepEqual(calls, ['/api/status']);
  const event = new document.defaultView.MouseEvent('click', { bubbles: true, cancelable: true });
  document.getElementById('connect').dispatchEvent(event);
  assert.equal(event.defaultPrevented, true);
  assert.equal(document.getElementById('setup-view').hidden, false);
  assert.equal(document.getElementById('overview-view').hidden, true);
  assert.equal(document.getElementById('export').hidden, true);
});
test('connected UI renders report/chart, escapes text and rejects arbitrary image hosts', async t => {
  const { document } = await setup(t, { connected: true, configured: true });
  assert.equal(document.getElementById('connect-banner').hidden, true);
  assert.equal(document.getElementById('channel-strip').hidden, false);
  assert.equal(document.getElementById('channel-title').textContent, fixture.channel.title);
  assert.equal(document.querySelector('#channel-title script'), null);
  assert.equal(document.getElementById('channel-avatar').getAttribute('src'), null);
  assert.equal(document.querySelector('#videos h3').textContent, fixture.videos[0].title);
  assert.equal(document.querySelector('#videos h3 img'), null);
  assert.equal(document.querySelectorAll('#videos .video-row').length, 1);
  assert.equal(document.getElementById('chart-svg').hasAttribute('hidden'), false);
  assert.equal(document.querySelectorAll('#chart-svg circle').length, 2);
  assert.equal(document.getElementById('export').hidden, false);
  assert.notEqual(document.getElementById('metric-views').textContent, '—');
});
test('partial data stays blank and warns about wrong channel and unavailable analytics', async t => {
  const data = { ...fixture, expectedChannel: false, analytics: null, videos: [], warnings: ['analytics_unavailable'] };
  const { document } = await setup(t, { connected: true, configured: true, data });
  assert.equal(document.getElementById('metric-views').textContent, '—');
  assert.equal(document.getElementById('chart-svg').hasAttribute('hidden'), true);
  assert.match(document.getElementById('notice').textContent, /@AhangBan/);
  assert.match(document.getElementById('notice').textContent, /Analytics/);
  assert.equal(document.getElementById('video-empty').hidden, false);
});
