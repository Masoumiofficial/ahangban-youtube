import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, readFile, writeFile, rm, access } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { createHash } from 'node:crypto';
import { createServer } from 'node:http';
import { validateJob, makeMetadata, chooseChannel, downloadAsset, validateSessionUrl, acknowledgedOffset, resumableUpload, readReceipt, writeReceipt, checkReceipt, authorize, publish, SCOPES } from '../tools/youtube-publisher.mjs';
const realJob = JSON.parse(await readFile(new URL('../tools/youtube-publish-job.json', import.meta.url), 'utf8'));
// These IDs and credentials are SYNTHETIC fixtures, never sent to Google.
const channelId = 'UC' + 'x'.repeat(22), videoId = 'AbCDeFGhI12';
const sessionUrl = 'https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&upload_id=FAKE';
const hash = x => createHash('sha256').update(x).digest('hex');
const json = (data, status = 200, headers = {}) => new Response(JSON.stringify(data), { status, headers: { 'Content-Type': 'application/json', ...headers } });
async function fixture(t) {
  const dir = await mkdtemp(join(tmpdir(), 'ahangban-publisher-test-')); t.after(() => rm(dir, { recursive: true, force: true }));
  const data = Buffer.from('synthetic video bytes, NOT a real upload');
  const image = Buffer.from('synthetic thumbnail'); const job = structuredClone(realJob);
  job.assets.video.bytes = data.length; job.assets.video.sha256 = hash(data);
  job.assets.thumbnail.bytes = image.length; job.assets.thumbnail.sha256 = hash(image);
  const video = join(dir, 'video.mp4'), thumbnail = join(dir, 'thumbnail.jpg');
  await writeFile(video, data); await writeFile(thumbnail, image);
  return { dir, data, image, job, video, thumbnail, receipt: join(dir, 'receipt.json') };
}

test('production job matches exact final009 files, not the rejected edit', async () => {
  assert.equal(validateJob(realJob).id, 'ahangban-009');
  for (const a of Object.values(realJob.assets)) {
    const data = await readFile(new URL('../' + a.path, import.meta.url));
    assert.equal(hash(data), a.sha256); assert.equal(data.length, a.bytes);
  }
  assert.equal(realJob.expectedChannelHandle, '@AhangBan');
  assert.match(realJob.description, /00:11 کجایی/);
});
test('explicit visibility and audience confirmation required; metadata truthful', () => {
  assert.throws(() => makeMetadata(realJob, undefined, true), /explicit_visibility/);
  assert.throws(() => makeMetadata(realJob, 'public', false), /audience/);
  const m = makeMetadata(realJob, 'public', true);
  assert.equal(m.status.privacyStatus, 'public'); assert.equal(m.status.selfDeclaredMadeForKids, false);
  assert.equal(m.status.containsSyntheticMedia, true); assert.equal(m.snippet.categoryId, '10');
  assert.equal(makeMetadata(realJob, 'private', true).status.privacyStatus, 'private');
});
test('only AhangBan owner channel accepted; no guessed channel ID', () => {
  assert.throws(() => chooseChannel({ items: [{ id: channelId, snippet: { customUrl: '@other' } }] }, '@ahangban'), /wrong_or_missing/);
  const body = { items: [{ id: channelId, snippet: { customUrl: '@AhangBan' } }] };
  assert.equal(chooseChannel(body, '@ahangban').id, channelId);
  assert.throws(() => chooseChannel({ items: [...body.items, { id: channelId, snippet: { customUrl: '@another' } }] }, '@ahangban'), /wrong_or_missing/);
  assert.throws(() => chooseChannel({ items: [...body.items, ...body.items] }, '@ahangban'), /wrong_or_missing/);
});
test('job rejects arbitrary hosts/path traversal/invalid hashes before download', () => {
  for (const path of ['../.env', 'https://evil.invalid/a.mp4', 'downloads/../../secret.mp4']) {
    const job = structuredClone(realJob); job.assets.video.path = path; assert.throws(() => validateJob(job), /invalid_asset/);
  }
});
test('downloads are pinned, hash verified, and cached only when correct', async t => {
  const f = await fixture(t); let calls = 0;
  const fetchImpl = async url => { calls++; assert.match(url, new RegExp('/raw/' + realJob.sourceCommit + '/downloads/')); return new Response(f.data); };
  const path = await downloadAsset(f.job, 'video', f.dir, fetchImpl);
  assert.equal(hash(await readFile(path)), f.job.assets.video.sha256);
  await downloadAsset(f.job, 'video', f.dir, fetchImpl); assert.equal(calls, 1);
});
test('corrupt download removed and never uploaded', async t => {
  const f = await fixture(t);
  await assert.rejects(downloadAsset(f.job, 'video', f.dir, async () => new Response('bad')), /asset_hash_mismatch/);
  await assert.rejects(access(join(f.dir, 'ahangban-music-film-youtube.mp4.part')));
});
test('upload session endpoints/ranges fail closed', () => {
  for (const url of ['https://evil.invalid/upload/youtube/v3/videos', 'http://www.googleapis.com/upload/youtube/v3/videos', 'https://www.googleapis.com:444/upload/youtube/v3/videos', 'https://secret@www.googleapis.com/upload/youtube/v3/videos']) assert.throws(() => validateSessionUrl(url));
  assert.equal(validateSessionUrl(sessionUrl), sessionUrl);
  assert.equal(acknowledgedOffset(new Response(null, { status: 308, headers: { range: 'bytes=0-7' } }), 10), 8);
  assert.throws(() => acknowledgedOffset(new Response(null, { status: 308, headers: { range: 'bytes=0-100' } }), 10));
});
test('transient PUT failure reconciles same session and sends only remaining bytes', async t => {
  const f = await fixture(t); const requests = [];
  const fetchImpl = async (url, options) => {
    assert.equal(url, sessionUrl); requests.push(options.headers['Content-Range']);
    if (requests.length === 1) return new Response(null, { status: 503 });
    if (requests.length === 2) return new Response(null, { status: 308, headers: { range: 'bytes=0-3' } });
    assert.deepEqual(Buffer.from(options.body), f.data.subarray(4)); return json({ id: videoId });
  };
  const result = await resumableUpload({ file: f.video, bytes: f.data.length, sessionUrl, accessToken: 'FAKE', fetchImpl, sleep: async () => {} });
  assert.equal(result.id, videoId); assert.equal(requests[1], `bytes */${f.data.length}`); assert.equal(requests[2], `bytes 4-${f.data.length - 1}/${f.data.length}`);
});
test('receipts exclude secrets and block uncertain prior uploads', async t => {
  const f = await fixture(t);
  const receipt = { jobId: f.job.id, videoSha256: f.job.assets.video.sha256, channelId, state: 'upload_started', access_token: 'DO_NOT_SAVE', clientSecret: 'DO_NOT_SAVE', sessionUrl };
  await writeReceipt(f.receipt, receipt); const data = await readFile(f.receipt, 'utf8');
  assert.doesNotMatch(data, /DO_NOT_SAVE|upload_id|access_token|clientSecret/);
  assert.throws(() => checkReceipt(JSON.parse(data), f.job, channelId), /previous_upload_outcome_uncertain/);
});
test('wrong account stops before creating an upload', async t => {
  const f = await fixture(t); let calls = 0;
  await assert.rejects(publish({ job: f.job, videoFile: f.video, thumbnailFile: f.thumbnail, accessToken: 'FAKE', privacy: 'public', notMadeForKids: true, receiptPath: f.receipt,
    fetchImpl: async url => { calls++; assert.match(String(url), /channels\?/); return json({ items: [] }); } }), /wrong_or_missing/);
  assert.equal(calls, 1);
});
test('Google-forced private upload is NOT reported as public; thumbnail failure retains receipt', async t => {
  const f = await fixture(t); const calls = [];
  const fetchImpl = async (url, options = {}) => {
    const u = String(url); calls.push(u);
    if (u.includes('/channels?')) return json({ items: [{ id: channelId, snippet: { customUrl: '@ahangban' } }] });
    if (u.includes('uploadType=resumable&part=')) { assert.equal(JSON.parse(options.body).status.privacyStatus, 'public'); return new Response(null, { headers: { location: sessionUrl } }); }
    if (u === sessionUrl) return json({ id: videoId });
    if (u.includes('/thumbnails/set?')) return json({}, 403);
    if (u.includes('/videos?')) return json({ items: [{ id: videoId, snippet: { channelId, title: f.job.title }, status: { privacyStatus: 'private', uploadStatus: 'processed' }, processingDetails: { processingStatus: 'succeeded' } }] });
    throw new Error('Unexpected mocked request');
  };
  const result = await publish({ job: f.job, videoFile: f.video, thumbnailFile: f.thumbnail, accessToken: 'FAKE', privacy: 'public', notMadeForKids: true, receiptPath: f.receipt, fetchImpl });
  assert.equal(result.publicConfirmed, false); assert.equal(result.thumbnailSet, false);
  const saved = await readReceipt(f.receipt); assert.equal(saved.videoId, videoId); assert.equal(saved.actualPrivacy, 'private');
  await publish({ job: f.job, videoFile: f.video, thumbnailFile: f.thumbnail, accessToken: 'FAKE', privacy: 'public', notMadeForKids: true, receiptPath: f.receipt, fetchImpl });
  assert.equal(calls.filter(u => u.includes('uploadType=resumable&part=')).length, 1);
});
test('public confirmation requires successful processing, not just insert response', async t => {
  const f = await fixture(t); await writeReceipt(f.receipt, { jobId: f.job.id, videoSha256: f.job.assets.video.sha256, channelId, videoId, requestedPrivacy: 'public', state: 'uploaded', thumbnailSet: true });
  const fetchImpl = async url => String(url).includes('/channels?') ? json({ items: [{ id: channelId, snippet: { customUrl: '@ahangban' } }] }) : json({ items: [{ id: videoId, snippet: { channelId, title: f.job.title }, status: { privacyStatus: 'public', uploadStatus: 'uploaded' }, processingDetails: { processingStatus: 'processing' } }] });
  const result = await publish({ job: f.job, videoFile: f.video, thumbnailFile: f.thumbnail, accessToken: 'FAKE', privacy: 'public', notMadeForKids: true, receiptPath: f.receipt, fetchImpl, processingTimeout: 0 });
  assert.equal(result.publicConfirmed, false);
});
test('localhost OAuth checks state and PKCE; upload scope requires fresh consent', async () => {
  const reserve = createServer(); await new Promise(r => reserve.listen(0, '127.0.0.1', r)); const port = reserve.address().port;
  await new Promise(r => reserve.close(r)); let challenge;
  const accessToken = await authorize({ clientId: 'SYNTHETIC_CLIENT', clientSecret: 'SYNTHETIC_SECRET', baseUrl: `http://127.0.0.1:${port}`,
    openBrowser: async origin => {
      const response = await fetch(origin, { redirect: 'manual' }); const auth = new URL(response.headers.get('location'));
      assert.equal(auth.searchParams.get('prompt'), 'consent'); assert.equal(auth.searchParams.get('scope'), SCOPES.join(' '));
      assert.equal(auth.searchParams.has('access_type'), false); challenge = auth.searchParams.get('code_challenge');
      const invalid = await fetch(origin + '/auth/google/callback?code=FAKE&state=WRONG'); assert.equal(invalid.status, 400);
      await fetch(origin + '/auth/google/callback?code=FAKE&state=' + auth.searchParams.get('state'));
    },
    fetchImpl: async (url, options) => {
      assert.equal(url, 'https://oauth2.googleapis.com/token'); assert.equal(hash(Buffer.from(options.body.get('code_verifier'))), Buffer.from(challenge, 'base64url').toString('hex'));
      return json({ access_token: 'SYNTHETIC_ACCESS', scope: SCOPES.join(' ') });
    } });
  assert.equal(accessToken, 'SYNTHETIC_ACCESS');
});

test('Windows launcher pins the actual publisher and job bytes', async () => {
  const launcher = await readFile(new URL('../scripts/publish-youtube.ps1', import.meta.url), 'utf8');
  for (const path of ['tools/youtube-publisher.mjs', 'tools/youtube-publish-job.json']) {
    const data = await readFile(new URL('../' + path, import.meta.url)); assert.ok(launcher.includes(hash(data)));
  }
  assert.match(launcher, /--env-file=/); assert.match(launcher, /Get-FileHash/);
  assert.doesNotMatch(launcher, /Get-Content.*\.env|Stop-Process|taskkill/i);
});
test('successful public processing is confirmed only from actual status readback (mock)', async t => {
  const f = await fixture(t); await writeReceipt(f.receipt, { jobId: f.job.id, videoSha256: f.job.assets.video.sha256, channelId, videoId, requestedPrivacy: 'public', state: 'uploaded', thumbnailSet: true });
  const fetchImpl = async url => String(url).includes('/channels?') ? json({ items: [{ id: channelId, snippet: { customUrl: '@ahangban' } }] }) : json({ items: [{ id: videoId, snippet: { channelId, title: f.job.title }, status: { privacyStatus: 'public', uploadStatus: 'processed' }, processingDetails: { processingStatus: 'succeeded' } }] });
  const result = await publish({ job: f.job, videoFile: f.video, thumbnailFile: f.thumbnail, accessToken: 'FAKE', privacy: 'public', notMadeForKids: true, receiptPath: f.receipt, fetchImpl });
  assert.equal(result.publicConfirmed, true);
});
